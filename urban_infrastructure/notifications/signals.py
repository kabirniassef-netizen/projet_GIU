import mimetypes
import logging
import email.policy
from smtplib import SMTPException
from email.message import EmailMessage as MIMEEmailMessage
from html import escape

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from urban_infrastructure.incidents.models import Incident
from urban_infrastructure.interventions.models import Intervention

from .models import Notification


logger = logging.getLogger(__name__)
User = get_user_model()


class _InlineImageEmail(EmailMultiAlternatives):
    def __init__(self, *args, photo_name, photo_content, photo_mime_type, **kwargs):
        super().__init__(*args, **kwargs)
        self.photo_name = photo_name
        self.photo_content = photo_content
        self.photo_mime_type = photo_mime_type

    def message(self, *, policy=email.policy.default):
        message = super().message(policy=policy)
        text_part, html_part = message.iter_parts()
        related_part = MIMEEmailMessage(policy=policy)
        related_part.make_related()
        related_part.attach(html_part)
        maintype, subtype = self.photo_mime_type.split('/', 1)
        related_part.add_related(
            self.photo_content,
            maintype=maintype,
            subtype=subtype,
            cid='<incident-photo>',
            filename=self.photo_name,
            disposition='inline',
        )
        message.set_payload([text_part, related_part])
        return message


def _management_users():
    return User.objects.filter(
        Q(role__in=['manager', 'admin']) | Q(is_superuser=True),
        is_active=True,
    )


def _create_notifications(users, event_type, message, related_object):
    recipients = {user.pk: user for user in users if user and user.is_active}
    Notification.objects.bulk_create([
        Notification(
            recipient=user,
            event_type=event_type,
            message=message,
            related_object=related_object,
        )
        for user in recipients.values()
    ])
    email_messages = []
    sent_addresses = set()
    email_recipients = User.objects.filter(
        is_active=True,
    ).exclude(email='').order_by('pk')
    incident_photo = None
    if event_type == 'incident_created' and isinstance(related_object, Incident):
        incident_address = ', '.join(filter(None, (
            related_object.commune,
            related_object.department,
            related_object.region,
        ))) or related_object.address or 'Non renseignée'
        message = (
            f'Nouveau signalement : {related_object.title}\n\n'
            f'Titre : {related_object.title}\n'
            f'Description : {related_object.description}\n'
            f'Adresse : {incident_address}\n'
            f'Catégorie : {related_object.category.get_name_display()}\n'
            f'Priorité : {related_object.get_priority_display()}'
        )
        if related_object.photo:
            with related_object.photo.open('rb') as photo_file:
                photo_content = photo_file.read()
            photo_name = related_object.photo.name.rsplit('/', 1)[-1]
            photo_mime_type = (
                mimetypes.guess_type(photo_name)[0] or 'application/octet-stream'
            )
            incident_photo = (photo_name, photo_content, photo_mime_type)
    for user in recipients.values():
        if not user.email:
            logger.warning(
                'Cannot send %s notification by email to user %s: no email address',
                event_type,
                user.pk,
            )

    for user in email_recipients:
        email_address = user.email.strip()
        if not email_address:
            continue
        normalized_email = email_address.casefold()
        if normalized_email in sent_addresses:
            continue
        sent_addresses.add(normalized_email)
        greeting_name = user.get_full_name() or user.get_username()
        if incident_photo:
            body = (
                f'Bonjour {greeting_name},\n\n{message}\n\n'
                'Connectez-vous à GIU pour consulter les détails.'
            )
            email = _InlineImageEmail(
                f'GIU - {event_type.replace("_", " ").capitalize()}',
                body,
                settings.DEFAULT_FROM_EMAIL,
                [email_address],
                photo_name=photo_name,
                photo_content=photo_content,
                photo_mime_type=photo_mime_type,
            )
            html_body = (
                f'<html><body><p>{escape(body).replace(chr(10), "<br>")}</p>'
                '<p><img src="cid:incident-photo" '
                'alt="Photo du signalement" style="max-width: 600px;"></p>'
                '</body></html>'
            )
            email.attach_alternative(html_body, 'text/html')
        else:
            email = EmailMessage(
                f'GIU - {event_type.replace("_", " ").capitalize()}',
                f'Bonjour {greeting_name},\n\n{message}\n\n'
                'Connectez-vous à GIU pour consulter les détails.',
                settings.DEFAULT_FROM_EMAIL,
                [email_address],
            )
        email_messages.append(email)
    for email in email_messages:
        try:
            email.send(fail_silently=False)
        except (OSError, SMTPException):
            logger.exception(
                'Failed to send %s notification email to %s',
                event_type,
                ', '.join(email.to),
            )


@receiver(pre_save, sender=Incident)
def remember_incident_status(sender, instance, **kwargs):
    instance._previous_status = None
    if instance.pk:
        instance._previous_status = sender.objects.filter(pk=instance.pk).values_list(
            'status', flat=True,
        ).first()


@receiver(post_save, sender=Incident)
def notify_incident_events(sender, instance, created, **kwargs):
    if created:
        # Chaque nouveau signalement est annoncé à tous les utilisateurs actifs.
        _create_notifications(
            User.objects.filter(is_active=True),
            'incident_created',
            f'Nouveau signalement : {instance.title}',
            instance,
        )
        return

    if instance.status == instance._previous_status:
        return

    event_messages = {
        Incident.VALIDATED: ('incident_validated', 'Votre signalement a été validé.'),
        Incident.PLANNED: ('incident_planned', 'Votre signalement a été planifié.'),
        Incident.IN_PROGRESS: (
            'incident_in_progress',
            'Votre signalement est en cours de traitement.',
        ),
        Incident.RESOLVED: ('incident_resolved', 'Votre signalement a été résolu.'),
        Incident.REJECTED: ('incident_rejected', 'Votre signalement a été rejeté.'),
    }
    event = event_messages.get(instance.status)
    if event:
        _create_notifications([instance.reporter], event[0], event[1], instance)


@receiver(pre_save, sender=Intervention)
def remember_intervention_state(sender, instance, **kwargs):
    instance._previous_status = None
    instance._previous_assigned_to_id = None
    if instance.pk:
        previous = sender.objects.filter(pk=instance.pk).values(
            'status', 'assigned_to_id',
        ).first()
        if previous:
            instance._previous_status = previous['status']
            instance._previous_assigned_to_id = previous['assigned_to_id']


@receiver(post_save, sender=Intervention)
def notify_intervention_events(sender, instance, created, **kwargs):
    assigned_to_changed = (
        instance.assigned_to_id
        and instance.assigned_to_id != instance._previous_assigned_to_id
    )
    if assigned_to_changed:
        _create_notifications(
            [instance.assigned_to],
            'intervention_assigned',
            f'Une intervention vous a été assignée : {instance.incident.title}',
            instance,
        )

    if created or instance.status == instance._previous_status:
        return

    if instance.status == Intervention.IN_PROGRESS:
        _create_notifications(
            _management_users(),
            'intervention_in_progress',
            f'L’intervention sur « {instance.incident.title} » est en cours.',
            instance,
        )
    elif instance.status == Intervention.COMPLETED:
        _create_notifications(
            [instance.incident.reporter, *_management_users()],
            'intervention_completed',
            f'L’intervention sur « {instance.incident.title} » est terminée.',
            instance,
        )