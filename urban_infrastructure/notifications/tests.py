from datetime import timedelta
import io
import json
import tempfile
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from urban_infrastructure.incidents.models import Incident, IncidentCategory
from urban_infrastructure.interventions.models import Intervention

from .email_backends import BREVO_API_URL, BrevoEmailBackend
from .models import Notification


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

    def test_new_incident_notifies_all_active_users(self):
        inactive_user = get_user_model().objects.create_user(
            username='notification-inactive-app', password='test', is_active=False,
        )

        incident = self.create_incident()

        for user in (self.citizen, self.manager, self.other_citizen, self.agent):
            self.assertTrue(Notification.objects.filter(
                recipient=user,
                event_type='incident_created',
                object_id=incident.pk,
            ).exists())
        self.assertFalse(Notification.objects.filter(recipient=inactive_user).exists())

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
        self.assertTrue(Notification.objects.filter(
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
    def test_each_active_user_gets_new_incident_email_on_own_address(self):
        for user in (self.citizen, self.manager, self.other_citizen, self.agent):
            user.email = f'{user.username}@example.com'
            user.save(update_fields=['email'])

        self.create_incident()

        self.assertEqual(
            sorted(message.to for message in mail.outbox),
            sorted([f'{user.username}@example.com'] for user in (
                self.citizen, self.manager, self.other_citizen, self.agent,
            )),
        )
        for message in mail.outbox:
            user = get_user_model().objects.get(email=message.to[0])
            self.assertIn(f'Bonjour {user.username},', message.body)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='notifications@example.com',
    )
    def test_status_change_email_goes_only_to_reporter(self):
        self.citizen.email = 'citizen@example.com'
        self.citizen.save(update_fields=['email'])
        self.other_citizen.email = 'other@example.com'
        self.other_citizen.save(update_fields=['email'])
        incident = self.create_incident()
        mail.outbox.clear()

        incident.status = Incident.VALIDATED
        incident.save()

        self.assertEqual([message.to for message in mail.outbox], [['citizen@example.com']])

    @override_settings(
        EMAIL_BACKEND='urban_infrastructure.notifications.email_backends.BrevoEmailBackend',
        BREVO_API_KEY='brevo-test-key',
        DEFAULT_FROM_EMAIL='GIU <notifications@example.com>',
    )
    def test_brevo_backend_sends_email_through_http_api(self):
        self.citizen.email = 'citizen@example.com'
        self.citizen.save(update_fields=['email'])

        with patch(
            'urban_infrastructure.notifications.email_backends.urllib_request.urlopen',
        ) as urlopen:
            incident = self.create_incident()

        urlopen.assert_called_once()
        api_request = urlopen.call_args.args[0]
        self.assertEqual(api_request.full_url, 'https://api.brevo.com/v3/smtp/email')
        self.assertEqual(api_request.get_header('Api-key'), 'brevo-test-key')
        payload = json.loads(api_request.data.decode('utf-8'))
        self.assertEqual(
            payload['sender'], {'email': 'notifications@example.com', 'name': 'GIU'},
        )
        self.assertEqual(payload['to'], [{'email': 'citizen@example.com'}])
        self.assertIn(incident.title, payload['textContent'])

    def _brevo_photo_message(self, photo_name):
        message = mail.EmailMessage(
            'Sujet', 'Corps', 'notifications@example.com', ['citizen@example.com'],
        )
        message.photo_name = photo_name
        message.photo_content = b'fake-jpeg-content'
        return message

    @override_settings(BREVO_API_KEY='brevo-test-key')
    def test_brevo_backend_renames_jfif_photo_to_jpg(self):
        with patch(
            'urban_infrastructure.notifications.email_backends.urllib_request.urlopen',
        ) as urlopen:
            sent = BrevoEmailBackend().send_messages([self._brevo_photo_message('photo.jfif')])

        self.assertEqual(sent, 1)
        payload = json.loads(urlopen.call_args.args[0].data.decode('utf-8'))
        self.assertEqual(payload['attachment'][0]['name'], 'photo.jpg')

    @override_settings(BREVO_API_KEY='brevo-test-key')
    def test_brevo_backend_resends_without_attachment_when_rejected(self):
        rejection = HTTPError(
            BREVO_API_URL, 400, 'Bad Request', {},
            io.BytesIO(b'{"code":"invalid_parameter","message":"Unsupported file format"}'),
        )
        with patch(
            'urban_infrastructure.notifications.email_backends.urllib_request.urlopen',
            side_effect=[rejection, MagicMock()],
        ) as urlopen:
            sent = BrevoEmailBackend().send_messages([self._brevo_photo_message('photo.heic')])

        self.assertEqual(sent, 1)
        self.assertEqual(urlopen.call_count, 2)
        retry_payload = json.loads(urlopen.call_args.args[0].data.decode('utf-8'))
        self.assertNotIn('attachment', retry_payload)

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
