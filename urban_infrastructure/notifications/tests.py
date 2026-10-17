from datetime import timedelta
import hashlib
import hmac
import json
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient

from urban_infrastructure.incidents.notifications import (
    notify_administrators_about_incident_via_whatsapp,
    notify_reporter_about_incident_status_via_whatsapp,
)
from urban_infrastructure.incidents.models import Incident, IncidentCategory
from urban_infrastructure.interventions.models import Intervention

from .models import Notification, WhatsAppContact, WhatsAppMessage, WhatsAppTemplate


class NotificationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.citizen = user_model.objects.create_user(
            username='notification-citizen', password='test', role='citizen',
        )
        self.manager = user_model.objects.create_user(
            username='notification-manager', password='test', role='manager',
        )
        self.other_citizen = user_model.objects.create_user(
            username='notification-other', password='test', role='citizen',
        )
        self.agent = user_model.objects.create_user(
            username='notification-agent', password='test', role='agent',
        )
        self.category = IncidentCategory.objects.create(name='road')
        self.client = APIClient()

    def create_incident(self):
        return Incident.objects.create(
            title='Nid-de-poule',
            description='Chaussée dégradée',
            category=self.category,
            reporter=self.citizen,
        )

    def test_new_incident_notifies_managers(self):
        incident = self.create_incident()

        self.assertTrue(Notification.objects.filter(
            recipient=self.manager,
            event_type='incident_created',
            object_id=incident.pk,
        ).exists())
        self.assertFalse(Notification.objects.filter(recipient=self.agent).exists())

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='notifications@example.com',
    )
    def test_new_incident_sends_email_to_management_users(self):
        self.manager.first_name = 'Kabir'
        self.manager.last_name = 'Niasse'
        self.manager.email = 'manager@example.com'
        self.manager.save(update_fields=['first_name', 'last_name', 'email'])

        incident = self.create_incident()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['manager@example.com'])
        self.assertIn('Bonjour Kabir Niasse,', mail.outbox[0].body)
        self.assertIn(incident.title, mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, 'notifications@example.com')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='notifications@example.com',
    )
    def test_notification_emails_are_broadcast_to_all_active_users_once_per_address(self):
        self.citizen.email = 'citizen@example.com'
        self.citizen.save(update_fields=['email'])
        self.manager.email = 'shared@example.com'
        self.manager.save(update_fields=['email'])
        self.other_citizen.email = ' SHARED@example.com '
        self.other_citizen.save(update_fields=['email'])
        self.agent.email = 'agent@example.com'
        self.agent.save(update_fields=['email'])
        decision_maker = get_user_model().objects.create_user(
            username='notification-decision-maker',
            email='decision@example.com',
            role='decision_maker',
        )
        inactive_user = get_user_model().objects.create_user(
            username='notification-inactive',
            email='inactive@example.com',
            role='citizen',
            is_active=False,
        )

        incident = self.create_incident()

        self.assertEqual(
            {message.to[0] for message in mail.outbox},
            {
                'citizen@example.com',
                'shared@example.com',
                'agent@example.com',
                'decision@example.com',
            },
        )
        self.assertEqual(len(mail.outbox), 4)
        self.assertFalse(any(
            message.to == ['inactive@example.com']
            for message in mail.outbox
        ))
        self.assertTrue(Notification.objects.filter(
            recipient=self.manager,
            event_type='incident_created',
            object_id=incident.pk,
        ).exists())
        self.assertFalse(Notification.objects.filter(
            recipient=decision_maker,
            event_type='incident_created',
            object_id=incident.pk,
        ).exists())

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='notifications@example.com',
    )
    def test_management_recipients_sharing_an_email_get_one_message(self):
        shared_email = 'manager@example.com'
        self.manager.email = shared_email
        self.manager.save(update_fields=['email'])
        get_user_model().objects.create_user(
            username='notification-admin',
            email=shared_email,
            role='admin',
        )

        self.create_incident()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [shared_email])

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='notifications@example.com',
    )
    def test_new_incident_email_contains_details_and_embeds_photo(self):
        self.manager.email = 'manager@example.com'
        self.manager.save(update_fields=['email'])
        image = SimpleUploadedFile(
            'incident.png',
            b'fake-png-content',
            content_type='image/png',
        )

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                incident = Incident.objects.create(
                    title='Lampadaire en panne',
                    description='La lampe est endommagée.',
                    category=self.category,
                    reporter=self.citizen,
                    commune='Dakar',
                    department='Dakar',
                    region='Dakar',
                    photo=image,
                )

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Titre : Lampadaire en panne', email.body)
        self.assertIn('Description : La lampe est endommagée.', email.body)
        self.assertIn('Adresse : Dakar, Dakar, Dakar', email.body)
        self.assertIn('Catégorie : Voirie', email.body)
        self.assertEqual(len(email.alternatives), 1)
        html_body, content_type = email.alternatives[0]
        self.assertEqual(content_type, 'text/html')
        self.assertIn('src="cid:incident-photo"', html_body)

        message = email.message()
        self.assertEqual(message.get_content_type(), 'multipart/alternative')
        related = next(
            part for part in message.iter_parts()
            if part.get_content_type() == 'multipart/related'
        )
        self.assertIsNotNone(related)
        html_part = next(
            part for part in related.iter_parts()
            if part.get_content_type() == 'text/html'
        )
        self.assertIn('cid:incident-photo', html_part.get_content())
        image = next(
            part for part in related.walk()
            if part.get('Content-ID') == '<incident-photo>'
        )
        self.assertEqual(image.get_content_type(), 'image/png')
        self.assertEqual(image.get_filename(), 'incident.png')
        self.assertEqual(image.get_payload(decode=True), b'fake-png-content')
        self.assertTrue(image.get('Content-Disposition').startswith('inline'))

    @override_settings(
        INCIDENT_NOTIFICATION_PHONE_NUMBERS=['+33612345678'],
        WHATSAPP_API_VERSION='v25.0',
        WHATSAPP_PHONE_NUMBER_ID='business-phone-id',
        WHATSAPP_ACCESS_TOKEN='test-access-token',
        WHATSAPP_TEMPLATE_NAME='giu_new_incident',
        WHATSAPP_TEMPLATE_LANGUAGE='fr',
    )
    def test_incident_notification_can_use_whatsapp_cloud_api(self):
        incident = self.create_incident()
        self.manager.is_staff = True
        self.manager.phone_number = '+33612345678'
        self.manager.save(update_fields=['is_staff', 'phone_number'])
        contact = WhatsAppContact.objects.create(
            user=self.manager,
            phone_number=self.manager.phone_number,
            is_opted_in=True,
            opted_in_at=timezone.now(),
        )
        with patch(
            'urban_infrastructure.incidents.notifications.urllib_request.urlopen',
        ) as urlopen:
            response = urlopen.return_value.__enter__.return_value
            response.read.return_value = json.dumps({
                'messages': [{'id': 'wamid.test-message'}],
            }).encode('utf-8')

            sent_count = notify_administrators_about_incident_via_whatsapp(incident)

        self.assertEqual(sent_count, 1)
        api_request = urlopen.call_args.args[0]
        self.assertEqual(
            api_request.full_url,
            'https://graph.facebook.com/v25.0/business-phone-id/messages',
        )
        payload = json.loads(api_request.data.decode('utf-8'))
        self.assertEqual(payload['to'], '+33612345678')
        self.assertEqual(
            api_request.headers['Authorization'],
            'Bearer test-access-token',
        )
        self.assertEqual(payload['template']['name'], 'giu_new_incident')
        self.assertEqual(
            [item['text'] for item in payload['template']['components'][0]['parameters']],
            [
                str(incident.pk),
                incident.title,
                incident.category.get_name_display(),
                incident.get_priority_display(),
                'Non renseignée',
            ],
        )
        message = contact.messages.get()
        self.assertEqual(message.status, WhatsAppMessage.Status.SENT)
        self.assertEqual(message.provider_message_id, 'wamid.test-message')
        self.assertEqual(message.attempts, 1)
        self.assertEqual(message.related_id, str(incident.pk))

    @override_settings(
        WHATSAPP_PHONE_NUMBER_ID='business-phone-id',
        WHATSAPP_ACCESS_TOKEN='test-access-token',
    )
    def test_incident_status_notification_uses_reporter_template(self):
        incident = self.create_incident()
        contact = WhatsAppContact.objects.create(
            user=self.citizen,
            phone_number='+221771234567',
            is_opted_in=True,
        )
        template = WhatsAppTemplate.objects.create(
            event=WhatsAppTemplate.Event.INCIDENT_RESOLVED,
            template_name='incident_resolved',
            variables=['incident_id', 'status'],
        )
        incident.status = Incident.RESOLVED

        with patch(
            'urban_infrastructure.incidents.notifications.urllib_request.urlopen',
        ) as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = json.dumps({
                'messages': [{'id': 'wamid.resolved'}],
            }).encode('utf-8')
            sent_count = notify_reporter_about_incident_status_via_whatsapp(incident)

        self.assertEqual(sent_count, 1)
        payload = json.loads(urlopen.call_args.args[0].data.decode('utf-8'))
        self.assertEqual(payload['template']['name'], 'incident_resolved')
        self.assertEqual(
            [parameter['text'] for parameter in payload['template']['components'][0]['parameters']],
            [str(incident.pk), incident.get_status_display()],
        )
        self.assertEqual(
            contact.messages.get().template,
            template,
        )

    @override_settings(
        INCIDENT_NOTIFICATION_PHONE_NUMBERS=['+33612345678'],
        WHATSAPP_PHONE_NUMBER_ID='business-phone-id',
        WHATSAPP_ACCESS_TOKEN='test-access-token',
        WHATSAPP_TEMPLATE_NAME='giu_new_incident',
    )
    def test_whatsapp_notification_skips_contacts_without_opt_in(self):
        incident = self.create_incident()
        self.manager.is_staff = True
        self.manager.phone_number = '+33612345678'
        self.manager.save(update_fields=['is_staff', 'phone_number'])
        WhatsAppContact.objects.create(
            user=self.manager,
            phone_number=self.manager.phone_number,
        )

        with patch(
            'urban_infrastructure.incidents.notifications.urllib_request.urlopen',
        ) as urlopen:
            sent_count = notify_administrators_about_incident_via_whatsapp(incident)

        self.assertEqual(sent_count, 0)
        urlopen.assert_not_called()
        self.assertFalse(WhatsAppMessage.objects.exists())

    def test_incident_status_change_notifies_reporter(self):
        self.citizen.email = 'citizen@example.com'
        self.citizen.save(update_fields=['email'])
        incident = self.create_incident()
        incident.status = Incident.VALIDATED
        incident.save()

        self.assertTrue(Notification.objects.filter(
            recipient=self.citizen,
            event_type='incident_validated',
            object_id=incident.pk,
        ).exists())
        self.assertEqual(mail.outbox[-1].to, ['citizen@example.com'])
        self.assertIn('validé', mail.outbox[-1].body)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='notifications@example.com',
    )
    def test_status_api_sends_email_to_reporter(self):
        self.citizen.email = 'citizen@example.com'
        self.citizen.save(update_fields=['email'])
        incident = self.create_incident()
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            f'/api/incidents/incidents/{incident.pk}/update_status/',
            {'status': Incident.VALIDATED},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mail.outbox[-1].to, ['citizen@example.com'])
        self.assertIn('validé', mail.outbox[-1].body)

    def test_intervention_assignment_and_completion_notify_relevant_users(self):
        incident = self.create_incident()
        intervention = Intervention.objects.create(
            incident=incident,
            assigned_to=self.agent,
            scheduled_date=timezone.now() + timedelta(days=1),
            estimated_duration=60,
        )
        self.assertTrue(Notification.objects.filter(
            recipient=self.agent,
            event_type='intervention_assigned',
        ).exists())

        intervention.status = Intervention.IN_PROGRESS
        intervention.save()
        self.assertTrue(Notification.objects.filter(
            recipient=self.manager,
            event_type='intervention_in_progress',
        ).exists())

        intervention.status = Intervention.COMPLETED
        intervention.save()
        self.assertTrue(Notification.objects.filter(
            recipient=self.citizen,
            event_type='intervention_completed',
        ).exists())
        self.assertTrue(Notification.objects.filter(
            recipient=self.manager,
            event_type='intervention_completed',
        ).exists())

    def test_api_lists_only_own_notifications_and_marks_read(self):
        notification = Notification.objects.create(
            recipient=self.citizen,
            event_type='incident_validated',
            message='Signalement validé',
        )
        Notification.objects.create(
            recipient=self.other_citizen,
            event_type='incident_validated',
            message='Privé',
        )
        self.client.force_authenticate(self.citizen)

        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], notification.pk)

        response = self.client.patch(
            f'/api/notifications/{notification.pk}/',
            {'is_read': True},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_user_cannot_read_another_users_notification(self):
        notification = Notification.objects.create(
            recipient=self.other_citizen,
            event_type='incident_validated',
            message='Privé',
        )
        self.client.force_authenticate(self.citizen)

        response = self.client.patch(
            f'/api/notifications/{notification.pk}/',
            {'is_read': True},
            format='json',
        )
        self.assertEqual(response.status_code, 404)


class WhatsAppModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='whatsapp-contact-user',
            password='test',
        )
        self.contact = WhatsAppContact.objects.create(
            user=self.user,
            phone_number='+221771234567',
        )

    def test_contact_validates_e164_phone_number(self):
        self.contact.phone_number = '771234567'
        with self.assertRaises(ValidationError):
            self.contact.full_clean()

    def test_contact_records_opt_in_and_opt_out(self):
        self.contact.opt_in()
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.is_opted_in)
        self.assertIsNotNone(self.contact.opted_in_at)
        self.assertIsNone(self.contact.opted_out_at)

        self.contact.opt_out()
        self.contact.refresh_from_db()
        self.assertFalse(self.contact.is_opted_in)
        self.assertIsNotNone(self.contact.opted_out_at)

    def test_contact_service_window_expires_after_24_hours(self):
        self.assertFalse(self.contact.in_service_window)
        self.contact.last_inbound_at = timezone.now() - timedelta(hours=23)
        self.assertTrue(self.contact.in_service_window)
        self.contact.last_inbound_at = timezone.now() - timedelta(hours=24)
        self.assertFalse(self.contact.in_service_window)

    def test_message_tracks_send_and_failure_attempts(self):
        template = WhatsAppTemplate.objects.create(
            event=WhatsAppTemplate.Event.INCIDENT_CREATED,
            template_name='incident_created',
            variables=['incident_id'],
        )
        message = WhatsAppMessage.objects.create(
            contact=self.contact,
            template=template,
            payload={'incident_id': '42'},
        )

        message.mark_sent('wamid.test-message')
        message.mark_failed('temporary_error', 'Delivery failed')
        message.refresh_from_db()

        self.assertEqual(message.status, WhatsAppMessage.Status.FAILED)
        self.assertEqual(message.provider_message_id, 'wamid.test-message')
        self.assertEqual(message.error_code, 'temporary_error')
        self.assertEqual(message.error_message, 'Delivery failed')
        self.assertEqual(message.attempts, 2)
        self.assertIsNotNone(message.sent_at)


@override_settings(
    WHATSAPP_APP_SECRET='webhook-test-secret',
    WHATSAPP_WEBHOOK_VERIFY_TOKEN='verify-test-token',
)
class WhatsAppWebhookTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='webhook-contact-user',
            password='test',
        )
        self.contact = WhatsAppContact.objects.create(
            user=self.user,
            phone_number='+221771234567',
            is_opted_in=True,
        )
        self.message = WhatsAppMessage.objects.create(
            contact=self.contact,
            status=WhatsAppMessage.Status.SENT,
            provider_message_id='wamid.webhook-test',
        )
        self.client = Client()
        self.url = reverse('whatsapp_webhook')

    def sign_payload(self, body):
        digest = hmac.new(
            b'webhook-test-secret',
            body,
            hashlib.sha256,
        ).hexdigest()
        return f'sha256={digest}'

    def post_signed(self, payload):
        body = json.dumps(payload).encode('utf-8')
        return self.client.post(
            self.url,
            body,
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=self.sign_payload(body),
        )

    def test_webhook_verification_returns_meta_challenge(self):
        response = self.client.get(self.url, {
            'hub.mode': 'subscribe',
            'hub.verify_token': 'verify-test-token',
            'hub.challenge': 'challenge-value',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'challenge-value')

    def test_webhook_rejects_invalid_signature(self):
        response = self.client.post(
            self.url,
            b'{"entry":[]}',
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256='sha256=invalid',
        )

        self.assertEqual(response.status_code, 403)

    def test_webhook_updates_delivery_and_read_status(self):
        timestamp = str(int(timezone.now().timestamp()))
        response = self.post_signed({
            'entry': [{
                'changes': [{
                    'value': {
                        'statuses': [
                            {
                                'id': 'wamid.webhook-test',
                                'status': 'delivered',
                                'timestamp': timestamp,
                            },
                            {
                                'id': 'wamid.webhook-test',
                                'status': 'read',
                                'timestamp': timestamp,
                            },
                        ],
                    },
                }],
            }],
        })

        self.assertEqual(response.status_code, 200)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, WhatsAppMessage.Status.READ)
        self.assertIsNotNone(self.message.delivered_at)
        self.assertIsNotNone(self.message.read_at)

    def test_webhook_failure_status_stores_provider_error(self):
        response = self.post_signed({
            'entry': [{
                'changes': [{
                    'value': {
                        'statuses': [{
                            'id': 'wamid.webhook-test',
                            'status': 'failed',
                            'errors': [{
                                'code': 131026,
                                'error_data': {'details': 'Recipient unavailable'},
                            }],
                        }],
                    },
                }],
            }],
        })

        self.assertEqual(response.status_code, 200)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, WhatsAppMessage.Status.FAILED)
        self.assertEqual(self.message.error_code, '131026')
        self.assertEqual(self.message.error_message, 'Recipient unavailable')

    def test_inbound_message_opens_window_and_stop_revokes_consent(self):
        response = self.post_signed({
            'entry': [{
                'changes': [{
                    'value': {
                        'messages': [{
                            'from': '221771234567',
                            'timestamp': str(int(timezone.now().timestamp())),
                            'text': {'body': 'STOP'},
                        }],
                    },
                }],
            }],
        })

        self.assertEqual(response.status_code, 200)
        self.contact.refresh_from_db()
        self.assertFalse(self.contact.is_opted_in)
        self.assertIsNotNone(self.contact.opted_out_at)
        self.assertTrue(self.contact.in_service_window)