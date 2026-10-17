from django.conf import settings
import re
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


E164_REGEX = re.compile(r'^\+[1-9]\d{7,14}$')


def validate_e164(value: str) -> None:
    if not E164_REGEX.match(value):
        raise ValidationError(
            'Le numéro doit être au format international, ex. +221771234567.',
        )


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    event_type = models.CharField(max_length=50)
    message = models.CharField(max_length=500)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['recipient', 'is_read'])]

    def __str__(self):
        return f'{self.recipient}: {self.message}'


class WhatsAppContact(models.Model):
    """Numéro WhatsApp d'un utilisateur et preuve de son consentement."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='whatsapp_contact',
    )
    phone_number = models.CharField(
        'Numéro WhatsApp',
        max_length=16,
        unique=True,
        validators=[validate_e164],
    )
    is_opted_in = models.BooleanField('Consentement donné', default=False)
    opted_in_at = models.DateTimeField(null=True, blank=True)
    opted_out_at = models.DateTimeField(null=True, blank=True)
    last_inbound_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contact WhatsApp'
        verbose_name_plural = 'Contacts WhatsApp'

    def __str__(self) -> str:
        return f'{self.user} ({self.phone_number})'

    def opt_in(self) -> None:
        self.is_opted_in = True
        self.opted_in_at = timezone.now()
        self.opted_out_at = None
        self.save(update_fields=[
            'is_opted_in',
            'opted_in_at',
            'opted_out_at',
            'updated_at',
        ])

    def opt_out(self) -> None:
        self.is_opted_in = False
        self.opted_out_at = timezone.now()
        self.save(update_fields=['is_opted_in', 'opted_out_at', 'updated_at'])

    @property
    def in_service_window(self) -> bool:
        """True si l'utilisateur a écrit il y a moins de 24 h."""
        if not self.last_inbound_at:
            return False
        return timezone.now() - self.last_inbound_at < timedelta(hours=24)


class WhatsAppTemplate(models.Model):
    """Modèle de message approuvé par WhatsApp (obligatoire hors fenêtre 24 h)."""

    class Event(models.TextChoices):
        INCIDENT_CREATED = 'incident_created', 'Incident créé'
        INCIDENT_UPDATED = 'incident_updated', 'Incident mis à jour'
        INCIDENT_RESOLVED = 'incident_resolved', 'Incident résolu'

    event = models.CharField(max_length=40, choices=Event.choices, unique=True)
    template_name = models.CharField(max_length=100)
    language_code = models.CharField(max_length=10, default='fr')
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Modèle WhatsApp'
        verbose_name_plural = 'Modèles WhatsApp'

    def __str__(self) -> str:
        return f'{self.template_name} ({self.language_code})'


class WhatsAppMessage(models.Model):
    """Journal de chaque message envoyé, avec son statut de livraison."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        SENT = 'sent', 'Envoyé'
        DELIVERED = 'delivered', 'Délivré'
        READ = 'read', 'Lu'
        FAILED = 'failed', 'Échec'

    contact = models.ForeignKey(
        WhatsAppContact,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    template = models.ForeignKey(
        WhatsAppTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='messages',
    )
    body = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    provider_message_id = models.CharField(max_length=128, blank=True, db_index=True)
    error_code = models.CharField(max_length=32, blank=True)
    error_message = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    related_model = models.CharField(max_length=100, blank=True)
    related_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['related_model', 'related_id'])]
        verbose_name = 'Message WhatsApp'
        verbose_name_plural = 'Messages WhatsApp'

    def __str__(self) -> str:
        return f'{self.contact.phone_number} – {self.status}'

    def mark_sent(self, provider_message_id: str) -> None:
        self.status = self.Status.SENT
        self.provider_message_id = provider_message_id
        self.sent_at = timezone.now()
        self.attempts += 1
        self.save()

    def mark_failed(self, code: str = '', message: str = '') -> None:
        self.status = self.Status.FAILED
        self.error_code = code
        self.error_message = message
        self.attempts += 1
        self.save()