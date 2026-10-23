import os
import subprocess
import sys
from datetime import timedelta
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from PIL import Image

from scripts.load_test_data import populate_test_data
from urban_infrastructure.incidents.models import Incident, IncidentCategory
from urban_infrastructure.interventions.models import Intervention, InterventionUpdate
from urban_infrastructure.assets.models import AssetType


@override_settings(DEBUG=True, CITIZEN_HOME_ONLY=False)
class ProjectBootstrapTests(TestCase):
    def test_django_admin_login_page_is_available(self):
        client = Client()

        response = client.get('/admin/login/')

        self.assertEqual(response.status_code, 200)

    def test_production_settings_can_store_uploaded_photos(self):
        env = {
            **os.environ,
            'DEBUG': 'False',
            'SECRET_KEY': 'production-settings-test-key-0123456789-abcdefghijklmnop',
        }
        result = subprocess.run(
            [sys.executable, '-c', "from config import settings; print(sorted(settings.STORAGES))"],
            cwd=settings.BASE_DIR, env=env, capture_output=True, text=True, check=True,
        )

        self.assertIn("'default'", result.stdout)

    @override_settings(CITIZEN_HOME_ONLY=True)
    def test_hosted_home_page_only_shows_citizen_features(self):
        home = Client().get('/')

        self.assertEqual(home.status_code, 200)
        self.assertContains(home, 'href="/signaler/"')
        self.assertContains(home, 'href="/suivi/"')
        self.assertContains(home, 'id="reportModal"')
        self.assertNotContains(home, '/dashboard/')
        self.assertNotContains(home, 'href="/admin/"')
        self.assertNotContains(home, 'href="/api/"')
        self.assertNotContains(home, 'href="/login/"')
        self.assertNotContains(home, 'id="modules"')

    def test_citizen_reporting_links_open_the_form_with_photo_upload(self):
        client = Client()

        home = client.get('/')
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, 'href="/signaler/"')
        for module in ('users', 'assets', 'interventions', 'decisions', 'reports'):
            self.assertContains(home, f'href="/dashboard/?module={module}"')
        self.assertNotContains(home, 'href="/api/incidents/"')
        self.assertNotContains(home, 'href="/api/users/"')
        self.assertNotContains(home, 'href="/api/assets/"')
        self.assertNotContains(home, 'href="/api/interventions/"')
        self.assertNotContains(home, 'href="/api/reports/"')

        public_report = client.get('/signaler/')
        self.assertEqual(public_report.status_code, 200)
        self.assertContains(public_report, 'id="publicIncidentForm"')
        self.assertNotContains(public_report, 'reporter_phone')
        self.assertNotContains(public_report, 'reporter_name')
        self.assertNotContains(public_report, 'Vos coordonnées')
        self.assertNotContains(public_report, 'id="incidentAddress"')
        self.assertContains(public_report, 'id="incidentRegion"')
        self.assertContains(public_report, 'id="incidentDepartment"')
        self.assertContains(public_report, 'id="incidentCommune"')
        self.assertRedirects(
            client.get('/dashboard/?signalement=1'),
            '/signaler/',
            fetch_redirect_response=False,
        )

        dashboard = client.get('/dashboard/')
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, 'id="moduleSection"')
        self.assertContains(dashboard, 'id="incidentForm" enctype="multipart/form-data"')
        self.assertContains(dashboard, 'id="incidentPhoto" type="file"')
        self.assertContains(dashboard, 'id="incidentAddress"')
        self.assertNotContains(dashboard, '<th>Lieu</th>')
        self.assertContains(dashboard, 'En cas de blessé ou de danger immédiat')
        self.assertContains(
            dashboard,
            "new URLSearchParams(window.location.search).get('signalement')==='1'",
        )
        login = client.get('/login/')
        for module in ('users', 'assets', 'interventions', 'decisions', 'reports'):
            self.assertContains(login, f'/dashboard/?module={module}')

    def test_seed_data_creates_admin_and_default_users(self):
        User = get_user_model()
        User.objects.all().delete()

        populate_test_data()

        self.assertTrue(User.objects.filter(username='admin').exists())
        self.assertTrue(User.objects.filter(username='citoyen1').exists())
        self.assertTrue(User.objects.filter(username='agent1').exists())
        self.assertTrue(User.objects.filter(username='manager1').exists())
        self.assertTrue(User.objects.filter(username='decision1').exists())

    def test_seed_data_does_not_overwrite_existing_admin_or_run_in_production(self):
        User = get_user_model()
        admin = User.objects.create_user(
            username='admin',
            password='custom-admin-password',
            role='citizen',
        )

        populate_test_data()
        admin.refresh_from_db()
        self.assertEqual(admin.role, 'citizen')
        self.assertTrue(admin.check_password('custom-admin-password'))

        with override_settings(DEBUG=False):
            with self.assertRaisesRegex(RuntimeError, 'ne peuvent pas être chargées en production'):
                populate_test_data()

    def test_public_registration_and_login_work(self):
        client = Client()
        payload = {
            'username': 'newcitizen',
            'email': 'newcitizen@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'Citizen',
            'phone_number': '0102030405',
        }

        register_response = client.post('/api/users/users/', payload)
        self.assertEqual(register_response.status_code, 201)

        login_response = client.post('/api/auth/login/', {
            'username': 'newcitizen',
            'password': 'Password123!',
        })
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('token', login_response.json())

    def test_login_page_offers_public_citizen_registration(self):
        response = Client().get('/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="registrationForm"')
        self.assertContains(response, 'Créer un compte citoyen')
        self.assertContains(response, 'registrationPasswordConfirm')
        self.assertContains(
            response,
            "window.location.href = '/dashboard/?signalement=1'",
        )


@override_settings(DEBUG=True)
class ProjectBusinessFlowTests(TestCase):
    def setUp(self):
        populate_test_data()
        self.client = Client()
        self.User = get_user_model()
        self.citizen = self.User.objects.get(username='citoyen1')
        self.manager = self.User.objects.get(username='manager1')
        self.agent = self.User.objects.get(username='agent1')
        self.category = IncidentCategory.objects.first()

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='notifications@example.com',
    )
    def test_citizen_can_create_incident_and_view_his_incidents(self):
        self.client.force_login(self.citizen)
        self.manager.is_staff = True
        self.manager.email = 'manager@example.com'
        self.manager.save(update_fields=['is_staff', 'email'])
        response = self.client.post('/api/incidents/incidents/', {
            'title': 'Panne d\'éclairage test',
            'description': 'Le lampadaire ne s\'allume plus.',
            'category': self.category.id,
            'region': 'Île-de-France',
            'department': 'Paris',
            'commune': 'Paris',
        })

        self.assertEqual(response.status_code, 201)
        incident_id = response.json()['id']
        manager_email = next(
            message for message in mail.outbox
            if message.to == ['manager@example.com']
        )
        self.assertIn("Panne d'éclairage test", manager_email.body)

        incident_list = self.client.get('/api/incidents/incidents/my_incidents/')
        self.assertEqual(incident_list.status_code, 200)
        self.assertTrue(any(item['id'] == incident_id for item in incident_list.json()))
        incident = self.client.get(f'/api/incidents/incidents/{incident_id}/')
        self.assertEqual(incident.json()['region'], 'Île-de-France')
        self.assertEqual(incident.json()['department'], 'Paris')
        self.assertEqual(incident.json()['commune'], 'Paris')
        self.assertNotIn('latitude', incident.json())
        self.assertNotIn('longitude', incident.json())

    def test_incident_categories_include_requested_incident_types(self):
        self.client.force_login(self.citizen)
        categories = self.client.get('/api/incidents/categories/')
        self.assertEqual(categories.status_code, 200)
        labels = {
            item['name_display']
            for item in categories.json()['results']
        }
        self.assertTrue({
            'Imprudence',
            'Vitesse',
            'Panne',
            'Mauvaise visibilité',
            'Accident de la route',
        }.issubset(labels))

    def test_citizen_can_report_a_road_accident_with_a_precise_location(self):
        self.client.force_login(self.citizen)
        category = IncidentCategory.objects.get(name=IncidentCategory.ACCIDENT)

        response = self.client.post('/api/incidents/incidents/', {
            'title': 'Accident près du marché',
            'description': 'Collision observée vers 14 h, circulation ralentie.',
            'category': category.id,
            'address': 'Route nationale, près du marché central',
            'region': 'Dakar',
            'department': 'Dakar',
            'commune': 'Dakar',
        })

        self.assertEqual(response.status_code, 201)
        incident_id = response.json()['id']
        self.assertEqual(response.json()['address'], 'Route nationale, près du marché central')
        details = self.client.get(f'/api/incidents/incidents/{incident_id}/')
        self.assertEqual(details.status_code, 200)
        self.assertEqual(details.json()['category_display'], 'Accident de la route')
        self.assertEqual(details.json()['address'], 'Route nationale, près du marché central')
        incident_list = self.client.get('/api/incidents/incidents/my_incidents/')
        self.assertEqual(incident_list.status_code, 200)
        self.assertEqual(incident_list.json()[0]['address'], 'Route nationale, près du marché central')
        self.assertEqual(incident_list.json()[0]['title'], 'Accident près du marché')
        self.assertEqual(
            incident_list.json()[0]['description'],
            'Collision observée vers 14 h, circulation ralentie.',
        )

    def test_authenticated_non_citizen_can_submit_from_the_reporting_form(self):
        self.client.force_login(self.manager)

        response = self.client.post('/api/incidents/incidents/', {
            'title': 'Signalement envoyé depuis le tableau de bord',
            'description': 'Obstacle constaté sur la chaussée.',
            'category': self.category.id,
            'region': 'Dakar',
            'department': 'Dakar',
            'commune': 'Dakar',
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Incident.objects.get(pk=response.json()['id']).reporter,
            self.manager,
        )

        self.client.logout()
        anonymous_response = self.client.post('/api/incidents/incidents/', {
            'title': 'Signalement sans compte',
            'description': 'Ce signalement ne doit pas être créé.',
            'category': self.category.id,
            'region': 'Dakar',
            'department': 'Dakar',
            'commune': 'Dakar',
        })
        self.assertEqual(anonymous_response.status_code, 401)

    def test_anonymous_citizen_can_report_an_incident_without_contact_details(self):
        categories = self.client.get('/api/incidents/categories/')
        self.assertEqual(categories.status_code, 200)
        self.assertTrue(categories.json()['results'])

        category = IncidentCategory.objects.get(name=IncidentCategory.ACCIDENT)
        response = self.client.post('/api/incidents/public/', {
            'title': 'Accident près du marché',
            'description': 'Collision observée, circulation ralentie.',
            'category': category.id,
            'region': 'Dakar',
            'department': 'Dakar',
            'commune': 'Dakar',
        })

        self.assertEqual(response.status_code, 201)
        incident = Incident.objects.get(pk=response.json()['id'])
        self.assertIsNone(incident.reporter)
        self.assertEqual(incident.address, '')
        self.assertEqual(incident.region, 'Dakar')
        self.assertEqual(incident.department, 'Dakar')
        self.assertEqual(incident.commune, 'Dakar')
        self.assertEqual(incident.status, Incident.CREATED)
        self.assertIsNone(response.json()['reporter'])
        self.assertEqual(
            self.client.get('/api/incidents/incidents/').status_code,
            401,
        )

        invalid_response = self.client.post('/api/incidents/public/', {
            'title': 'Incident invalide',
            'category': category.id,
            'address': 'Dakar',
            'region': 'Dakar',
            'department': 'Dakar',
            'commune': 'Dakar',
        })
        self.assertEqual(invalid_response.status_code, 400)

    def test_public_report_works_while_a_session_is_open_in_the_browser(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)
        category = IncidentCategory.objects.get(name=IncidentCategory.ACCIDENT)

        response = client.post('/api/incidents/public/', {
            'title': 'Accident au rond-point',
            'description': 'Signalé depuis un navigateur connecté au tableau de bord.',
            'category': category.id,
            'region': 'Dakar',
            'department': 'Dakar',
            'commune': 'Dakar',
        })

        self.assertEqual(response.status_code, 201, response.content)
        self.assertIsNone(Incident.objects.get(pk=response.json()['id']).reporter)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    def test_anonymous_citizen_can_report_with_photo_when_email_delivery_fails(self):
        image_bytes = BytesIO()
        Image.new('RGB', (2, 2), color='red').save(image_bytes, format='JPEG')
        image = SimpleUploadedFile(
            'incident.jfif',
            image_bytes.getvalue(),
            content_type='image/jpeg',
        )
        category = IncidentCategory.objects.get(name=IncidentCategory.BREAKDOWN)

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with patch(
                    'django.core.mail.backends.smtp.EmailBackend.send_messages',
                    side_effect=OSError('SMTP server unavailable'),
                ) as send_messages:
                    response = self.client.post('/api/incidents/public/', {
                        'title': 'Une voiture qui s’arrête',
                        'description': 'Manque d’entretien.',
                        'category': category.id,
                        'region': 'DK',
                        'department': 'PA',
                        'commune': 'PA',
                        'photo': image,
                    })

                self.assertEqual(response.status_code, 201, response.content)
                send_messages.assert_called()
                incident = Incident.objects.get(pk=response.json()['id'])
                self.assertTrue(incident.photo)
                self.assertTrue(incident.photo.name.endswith('.jfif'))

    def test_manager_can_update_incident_status_and_public_stats_are_available(self):
        self.client.force_login(self.citizen)
        incident_response = self.client.post('/api/incidents/incidents/', {
            'title': 'Incident à valider',
            'description': 'À vérifier.',
            'category': self.category.id,
            'region': 'Île-de-France',
            'department': 'Paris',
            'commune': 'Paris',
        })
        incident_id = incident_response.json()['id']

        self.client.logout()
        self.client.force_login(self.manager)
        update_response = self.client.post(
            f'/api/incidents/incidents/{incident_id}/update_status/',
            {'status': 'validated', 'comment': 'Signalement validé'},
            content_type='application/json',
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()['status'], 'validated')

        stats = self.client.get('/api/reports/reports/global_statistics/')
        self.assertEqual(stats.status_code, 200)
        self.assertIn('total_incidents', stats.json())
        self.assertIn('resolved_incidents', stats.json())

    def test_only_managers_can_delete_incidents(self):
        self.client.force_login(self.citizen)
        incident_response = self.client.post('/api/incidents/incidents/', {
            'title': 'Incident à supprimer',
            'description': 'Test de suppression.',
            'category': self.category.id,
            'region': 'Île-de-France',
            'department': 'Paris',
            'commune': 'Paris',
        })
        incident_id = incident_response.json()['id']
        incident = Incident.objects.get(pk=incident_id)
        intervention = Intervention.objects.create(
            incident=incident,
            scheduled_date=timezone.now() + timedelta(days=1),
            estimated_duration=60,
        )
        intervention_update = InterventionUpdate.objects.create(
            intervention=intervention,
            status=Intervention.PENDING,
            comment='Mise à jour liée au signalement.',
        )

        citizen_delete_response = self.client.delete(
            f'/api/incidents/incidents/{incident_id}/',
        )
        self.assertEqual(citizen_delete_response.status_code, 403)
        self.assertTrue(Incident.objects.filter(pk=incident_id).exists())

        self.client.logout()
        self.client.force_login(self.manager)
        manager_delete_response = self.client.delete(
            f'/api/incidents/incidents/{incident_id}/',
        )
        self.assertEqual(manager_delete_response.status_code, 204)
        self.assertFalse(Incident.objects.filter(pk=incident_id).exists())
        self.assertFalse(Intervention.objects.filter(pk=intervention.pk).exists())
        self.assertFalse(InterventionUpdate.objects.filter(pk=intervention_update.pk).exists())

    def test_manager_can_create_intervention_for_incident(self):
        self.client.force_login(self.citizen)
        incident_response = self.client.post('/api/incidents/incidents/', {
            'title': 'Incident intervention',
            'description': 'Intervention nécessaire',
            'category': self.category.id,
            'region': 'Île-de-France',
            'department': 'Paris',
            'commune': 'Paris',
        })
        incident_id = incident_response.json()['id']

        self.client.logout()
        self.client.force_login(self.manager)
        self.client.post(
            f'/api/incidents/incidents/{incident_id}/update_status/',
            {'status': 'validated', 'comment': 'Validation avant planification'},
            content_type='application/json',
        )
        intervention_response = self.client.post('/api/interventions/interventions/', {
            'incident': incident_id,
            'assigned_to': self.agent.id,
            'scheduled_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'estimated_duration': 90,
            'priority': 'high',
            'notes': 'Intervention planifiée',
        })

        self.assertEqual(intervention_response.status_code, 201)
        self.assertEqual(intervention_response.json()['incident'], incident_id)
        self.assertEqual(intervention_response.json()['assigned_to'], self.agent.id)
        self.assertEqual(intervention_response.json()['status'], 'assigned')

    def test_agent_can_view_and_update_his_interventions(self):
        self.client.force_login(self.citizen)
        incident_response = self.client.post('/api/incidents/incidents/', {
            'title': 'Incident agent',
            'description': 'À traiter.',
            'category': self.category.id,
            'region': 'Île-de-France',
            'department': 'Paris',
            'commune': 'Paris',
        })
        incident_id = incident_response.json()['id']

        self.client.logout()
        self.client.force_login(self.manager)
        self.client.post(
            f'/api/incidents/incidents/{incident_id}/update_status/',
            {'status': 'validated', 'comment': 'Validation avant planification'},
            content_type='application/json',
        )
        intervention_response = self.client.post('/api/interventions/interventions/', {
            'incident': incident_id,
            'assigned_to': self.agent.id,
            'scheduled_date': (timezone.now() + timedelta(days=2)).isoformat(),
            'estimated_duration': 60,
            'priority': 'medium',
            'notes': 'Mission assignée',
        })
        intervention_id = intervention_response.json()['id']

        self.client.logout()
        self.client.force_login(self.agent)
        list_response = self.client.get('/api/interventions/interventions/my_interventions/')
        self.assertEqual(list_response.status_code, 200)
        intervention_items = list_response.json()
        self.assertTrue(any(
            item['id'] == intervention_id
            for item in intervention_items
        ))

        update_response = self.client.post(
            f'/api/interventions/interventions/{intervention_id}/update_status/',
            {'status': 'in_progress', 'comment': 'En cours sur site'},
            content_type='application/json',
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()['status'], 'in_progress')
        incident = self.client.get(f'/api/incidents/incidents/{incident_id}/')
        self.assertEqual(incident.json()['status'], 'in_progress')

        forbidden_update = self.client.post(
            f'/api/interventions/interventions/{intervention_id}/update_status/',
            {'status': 'cancelled'},
            content_type='application/json',
        )
        self.assertEqual(forbidden_update.status_code, 403)

        completion_response = self.client.post(
            f'/api/interventions/interventions/{intervention_id}/update_status/',
            {'status': 'completed', 'comment': 'Réparation terminée'},
            content_type='application/json',
        )
        self.assertEqual(completion_response.status_code, 200)
        incident = self.client.get(f'/api/incidents/incidents/{incident_id}/')
        self.assertEqual(incident.json()['status'], 'resolved')

    def test_incident_requires_structured_address_and_status_transitions_are_rejected(self):
        self.client.force_login(self.citizen)
        invalid_incident = self.client.post('/api/incidents/incidents/', {
            'title': 'Adresse incomplète',
            'description': 'Les champs d’adresse sont obligatoires.',
            'category': self.category.id,
        })
        self.assertEqual(invalid_incident.status_code, 400)

        incident = IncidentCategory.objects.first().incidents.create(
            title='Transition invalide',
            description='Test de transition.',
            reporter=self.citizen,
        )
        self.client.force_login(self.manager)
        response = self.client.post(
            f'/api/incidents/incidents/{incident.pk}/update_status/',
            {'status': 'resolved'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        incident.refresh_from_db()
        self.assertEqual(incident.status, Incident.CREATED)

    def test_decision_maker_can_read_but_not_manage_reports(self):
        decision_maker = self.User.objects.create_user(
            username='decision-reader',
            password='password123',
            role='decision_maker',
        )
        self.client.force_login(decision_maker)

        list_response = self.client.get('/api/reports/reports/')
        self.assertEqual(list_response.status_code, 200)
        dashboard_response = self.client.post(
            '/api/reports/reports/generate_dashboard/',
            content_type='application/json',
        )
        self.assertEqual(dashboard_response.status_code, 200)
        create_response = self.client.post('/api/reports/reports/', {})
        self.assertEqual(create_response.status_code, 403)

        incident_response = self.client.get('/api/incidents/incidents/')
        self.assertEqual(incident_response.status_code, 200)
        self.assertEqual(incident_response.json()['results'], [])

        intervention_response = self.client.get('/api/interventions/interventions/')
        self.assertEqual(intervention_response.status_code, 200)
        self.assertEqual(intervention_response.json()['results'], [])

    def test_asset_coordinates_outside_gps_bounds_are_rejected(self):
        asset_type = AssetType.objects.first()
        self.client.force_login(self.manager)
        response = self.client.post('/api/assets/assets/', {
            'code': 'GPS-INVALID',
            'name': 'Actif hors limites',
            'asset_type': asset_type.pk,
            'latitude': 91,
            'longitude': 2,
            'location': 'Test',
            'installed_date': '2026-01-01',
        })
        self.assertEqual(response.status_code, 400)

    def test_reports_endpoints_are_accessible(self):
        self.client.force_login(self.manager)
        stats = self.client.get('/api/reports/reports/global_statistics/')
        self.assertEqual(stats.status_code, 200)
        self.assertIn('total_incidents', stats.json())

        report = self.client.get('/api/reports/reports/')
        self.assertEqual(report.status_code, 200)


class EnsureAdminCommandTests(TestCase):
    @override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher'])
    def test_creates_admin_only_when_none_exists(self):
        call_command('ensure_admin', stdout=StringIO())
        call_command('ensure_admin', stdout=StringIO())

        admins = get_user_model().objects.filter(is_superuser=True)
        self.assertEqual(list(admins.values_list('username', flat=True)), ['admin'])
        self.assertTrue(admins.get().check_password('admin123'))
