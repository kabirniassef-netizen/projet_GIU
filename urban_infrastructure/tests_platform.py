"""Tests des fonctionnalités de gestion : comptes, suivi public, workflow et indicateurs."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from urban_infrastructure.assets.models import Asset, AssetHistory, AssetType
from urban_infrastructure.incidents.models import Incident, IncidentCategory
from urban_infrastructure.interventions.models import Intervention
from urban_infrastructure.notifications.models import Notification
from urban_infrastructure.reports.models import Report

User = get_user_model()


class PlatformTestCase(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.category, _ = IncidentCategory.objects.get_or_create(name='road')
        self.citizen = User.objects.create_user('citoyen', 'c@example.com', 'Password123!', role='citizen')
        self.other_citizen = User.objects.create_user('voisin', 'v@example.com', 'Password123!', role='citizen')
        self.agent = User.objects.create_user('agent', 'a@example.com', 'Password123!', role='agent', first_name='Awa', last_name='Diop')
        self.second_agent = User.objects.create_user('agent2', 'a2@example.com', 'Password123!', role='agent')
        self.manager = User.objects.create_user('manager', 'm@example.com', 'Password123!', role='manager')
        self.decision_maker = User.objects.create_user('decideur', 'd@example.com', 'Password123!', role='decision_maker')

    def as_user(self, user):
        self.api.force_authenticate(user)
        return self.api

    def create_incident(self, reporter=None, **extra):
        data = {
            'title': 'Nid de poule',
            'description': 'Chaussée dégradée',
            'category': self.category,
            'reporter': reporter or self.citizen,
            'region': 'Dakar',
            'department': 'Dakar',
            'commune': 'Plateau',
        }
        data.update(extra)
        return Incident.objects.create(**data)


class AccountManagementTests(PlatformTestCase):
    def test_superuser_session_exposes_effective_admin_role(self):
        User.objects.create_superuser('root', 'root@example.com', 'Password123!')

        response = APIClient().post('/api/auth/login/', {'username': 'root', 'password': 'Password123!'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['effective_role'], 'admin')
        self.assertTrue(response.json()['user']['is_superuser'])

    def test_login_accepts_email_address(self):
        response = APIClient().post('/api/auth/login/', {'username': 'c@example.com', 'password': 'Password123!'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], 'citoyen')

    def test_manager_creates_staff_account_but_public_signup_stays_citizen(self):
        response = self.as_user(self.manager).post('/api/users/users/', {
            'username': 'nouvel_agent', 'password': 'Sol1de-Passe!', 'role': 'agent',
            'first_name': 'Moussa', 'last_name': 'Ba',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.get(username='nouvel_agent').role, 'agent')
        self.assertIn('effective_role', response.json())

        public = APIClient().post('/api/users/users/', {
            'username': 'pirate', 'password': 'Sol1de-Passe!', 'role': 'admin',
        }, format='json')
        self.assertEqual(public.status_code, 201)
        self.assertEqual(User.objects.get(username='pirate').role, 'citizen')

    def test_only_admins_can_grant_admin_role(self):
        manager_api = self.as_user(self.manager)
        refused = manager_api.patch(f'/api/users/users/{self.agent.pk}/', {'role': 'admin'}, format='json')
        self.assertEqual(refused.status_code, 400)

        admin = User.objects.create_user('chef', 'chef@example.com', 'Password123!', role='admin')
        allowed = self.as_user(admin).post(f'/api/users/users/{self.agent.pk}/set_role/', {'role': 'manager'}, format='json')
        self.assertEqual(allowed.status_code, 200)
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.role, 'manager')

    def test_manager_can_deactivate_account_which_revokes_its_token(self):
        Token.objects.create(user=self.citizen)
        api = self.as_user(self.manager)

        response = api.post(f'/api/users/users/{self.citizen.pk}/toggle_active/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_active'])
        self.assertFalse(Token.objects.filter(user=self.citizen).exists())
        self_response = api.post(f'/api/users/users/{self.manager.pk}/toggle_active/')
        self.assertEqual(self_response.status_code, 400)

    def test_manager_resets_password_and_user_list_supports_search_and_counts(self):
        self.create_incident()
        api = self.as_user(self.manager)

        reset = api.post(f'/api/users/users/{self.citizen.pk}/reset_password/', {'new_password': 'Nouveau-Pass-42'}, format='json')
        self.assertEqual(reset.status_code, 200)
        self.citizen.refresh_from_db()
        self.assertTrue(self.citizen.check_password('Nouveau-Pass-42'))

        listing = api.get('/api/users/users/', {'role': 'citizen', 'search': 'citoyen'})
        self.assertEqual(listing.status_code, 200)
        rows = listing.json()['results']
        self.assertEqual([row['username'] for row in rows], ['citoyen'])
        self.assertEqual(rows[0]['incident_count'], 1)

        stats = api.get('/api/users/users/stats/')
        self.assertEqual(stats.json()['citizens_with_reports'], 1)
        self.assertEqual(self.as_user(self.agent).get('/api/users/users/stats/').status_code, 403)

    def test_user_updates_profile_changes_password_and_logs_out(self):
        api = self.as_user(self.citizen)
        profile = api.patch('/api/users/users/me/', {'first_name': 'Seynabou', 'role': 'admin'}, format='json')
        self.assertEqual(profile.status_code, 200)
        self.citizen.refresh_from_db()
        self.assertEqual(self.citizen.first_name, 'Seynabou')
        self.assertEqual(self.citizen.role, 'citizen')

        wrong = api.post('/api/users/users/change_password/', {'current_password': 'faux', 'new_password': 'Autre-Pass-99'}, format='json')
        self.assertEqual(wrong.status_code, 400)
        changed = api.post('/api/users/users/change_password/', {'current_password': 'Password123!', 'new_password': 'Autre-Pass-99'}, format='json')
        self.assertEqual(changed.status_code, 200)
        token = changed.json()['token']

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(client.post('/api/auth/logout/').status_code, 204)
        self.assertFalse(Token.objects.filter(key=token).exists())


class IncidentFeatureTests(PlatformTestCase):
    def test_public_tracking_exposes_status_without_personal_data(self):
        response = APIClient().post('/api/incidents/public/', {
            'title': 'Feu tricolore en panne', 'description': 'Carrefour dangereux',
            'category': self.category.pk, 'region': 'Dakar', 'department': 'Dakar', 'commune': 'Médina',
        })
        self.assertEqual(response.status_code, 201)
        code = response.json()['tracking_code']
        self.assertRegex(code, r'^GIU-[A-Z0-9]{8}$')

        tracking = APIClient().get(f'/api/incidents/track/{code.lower()}/')
        self.assertEqual(tracking.status_code, 200)
        data = tracking.json()
        self.assertEqual(data['status'], 'created')
        self.assertEqual(len(data['timeline']), 1)
        self.assertNotIn('reporter', data)
        self.assertNotIn('description', data)
        self.assertEqual(APIClient().get('/api/incidents/track/GIU-INCONNU0/').status_code, 404)
        self.assertEqual(self.client.get(f'/suivi/?code={code}').status_code, 200)

    @override_settings(CHATBOT_API_KEY='cle-du-bot')
    def test_chatbot_key_gets_its_own_quota(self):
        cache.clear()
        bot = APIClient(HTTP_X_CHATBOT_KEY='cle-du-bot')
        for _ in range(25):
            self.assertEqual(bot.get('/api/incidents/track/GIU-INCONNU0/').status_code, 404)

        wrong_key = APIClient(HTTP_X_CHATBOT_KEY='mauvaise-cle')
        statuses = [wrong_key.get('/api/incidents/track/GIU-INCONNU0/').status_code for _ in range(21)]
        self.assertEqual(statuses[-1], 429)
        cache.clear()

    def test_incident_list_filters_and_search(self):
        self.create_incident(title='Lampadaire éteint', priority='urgent')
        self.create_incident(title='Trottoir abîmé', status='validated')
        api = self.as_user(self.manager)

        by_status = api.get('/api/incidents/incidents/', {'status': 'validated'}).json()
        self.assertEqual([item['title'] for item in by_status['results']], ['Trottoir abîmé'])
        by_priority = api.get('/api/incidents/incidents/', {'priority': 'high,urgent'}).json()
        self.assertEqual([item['title'] for item in by_priority['results']], ['Lampadaire éteint'])
        by_search = api.get('/api/incidents/incidents/', {'search': 'lampadaire'}).json()
        self.assertEqual(by_search['count'], 1)
        self.assertIn('allowed_next_statuses', by_search['results'][0])

    def test_export_is_limited_to_reporting_roles(self):
        self.create_incident(title='Accident ; virgule')

        response = self.as_user(self.decision_maker).get('/api/incidents/incidents/export/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        body = response.content.decode('utf-8-sig')
        self.assertIn('Code de suivi', body)
        self.assertIn('"Accident ; virgule"', body)
        self.assertEqual(self.as_user(self.citizen).get('/api/incidents/incidents/export/').status_code, 403)

    def test_field_staff_comment_and_manager_edits_priority(self):
        incident = self.create_incident()
        api = self.as_user(self.manager)

        empty = api.post(f'/api/incidents/incidents/{incident.pk}/comment/', {'comment': '  '}, format='json')
        self.assertEqual(empty.status_code, 400)
        comment = api.post(f'/api/incidents/incidents/{incident.pk}/comment/', {'comment': 'Appel au citoyen'}, format='json')
        self.assertEqual(comment.status_code, 200)
        self.assertEqual(comment.json()['updates'][0]['comment'], 'Appel au citoyen')

        edit = api.patch(f'/api/incidents/incidents/{incident.pk}/', {'priority': 'urgent', 'status': 'resolved'}, format='json')
        self.assertEqual(edit.status_code, 200)
        self.assertEqual(edit.json()['priority'], 'urgent')
        self.assertEqual(edit.json()['status'], 'created')
        citizen_comment = self.as_user(self.citizen).post(f'/api/incidents/incidents/{incident.pk}/comment/', {'comment': 'x'}, format='json')
        self.assertEqual(citizen_comment.status_code, 403)


class InterventionWorkflowTests(PlatformTestCase):
    def plan(self, incident, agent=None):
        return self.as_user(self.manager).post('/api/interventions/interventions/', {
            'incident': incident.pk,
            'assigned_to': (agent or self.agent).pk,
            'scheduled_date': (timezone.now() + timedelta(days=1)).isoformat(),
            'estimated_duration': 45,
        }, format='json')

    def test_cancelled_intervention_returns_incident_for_replanning(self):
        incident = self.create_incident(status='validated')
        first = self.plan(incident)
        self.assertEqual(first.status_code, 201)

        cancel = self.as_user(self.manager).post(
            f"/api/interventions/interventions/{first.json()['id']}/update_status/",
            {'status': 'cancelled', 'comment': 'Météo défavorable'}, format='json')
        self.assertEqual(cancel.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.status, Incident.VALIDATED)

        second = self.plan(incident, agent=self.second_agent)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(incident.interventions.count(), 2)
        detail = self.as_user(self.manager).get(f'/api/incidents/incidents/{incident.pk}/').json()
        self.assertEqual(detail['intervention']['id'], second.json()['id'])

    def test_reassignment_and_agent_completion_with_report(self):
        incident = self.create_incident(status='validated')
        intervention_id = self.plan(incident).json()['id']

        reassigned = self.as_user(self.manager).patch(
            f'/api/interventions/interventions/{intervention_id}/',
            {'assigned_to': self.second_agent.pk}, format='json')
        self.assertEqual(reassigned.status_code, 200)
        self.assertEqual(reassigned.json()['assigned_to'], self.second_agent.pk)
        self.assertTrue(any('Réaffectée' in update['comment'] for update in reassigned.json()['updates']))
        self.assertEqual(self.as_user(self.agent).get(f'/api/interventions/interventions/{intervention_id}/').status_code, 404)

        agent_api = self.as_user(self.second_agent)
        agent_api.post(f'/api/interventions/interventions/{intervention_id}/update_status/', {'status': 'in_progress'}, format='json')
        done = agent_api.post(f'/api/interventions/interventions/{intervention_id}/update_status/', {'status': 'completed', 'comment': 'Rebouché'}, format='json')
        self.assertEqual(done.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.status, Incident.RESOLVED)
        active = agent_api.get('/api/interventions/interventions/', {'active': 'true'}).json()
        self.assertEqual(active['count'], 0)

    def test_completed_intervention_cannot_be_rescheduled(self):
        incident = self.create_incident(status='validated')
        intervention = Intervention.objects.get(pk=self.plan(incident).json()['id'])
        Intervention.objects.filter(pk=intervention.pk).update(status=Intervention.COMPLETED)

        response = self.as_user(self.manager).patch(
            f'/api/interventions/interventions/{intervention.pk}/', {'estimated_duration': 10}, format='json')

        self.assertEqual(response.status_code, 400)


class AssetAndReportingTests(PlatformTestCase):
    def setUp(self):
        super().setUp()
        self.asset_type, _ = AssetType.objects.get_or_create(name='lamp_post')
        self.asset = Asset.objects.create(
            code='LAMP-9', name='Lampadaire', asset_type=self.asset_type,
            location='Corniche', installed_date=timezone.localdate(),
        )

    def test_asset_status_change_is_logged_and_field_staff_record_maintenance(self):
        update = self.as_user(self.manager).patch(f'/api/assets/assets/{self.asset.pk}/', {'status': 'defective'}, format='json')
        self.assertEqual(update.status_code, 200)
        self.assertTrue(AssetHistory.objects.filter(asset=self.asset, action='status_change').exists())

        log = self.as_user(self.agent).post('/api/assets/history/', {
            'asset': self.asset.pk, 'action': 'repair', 'description': 'Ampoule remplacée', 'cost': '1500',
        }, format='json')
        self.assertEqual(log.status_code, 201)
        self.assertEqual(log.json()['performed_by'], self.agent.pk)
        self.assertEqual(self.as_user(self.citizen).post('/api/assets/history/', {
            'asset': self.asset.pk, 'action': 'repair', 'description': 'x',
        }, format='json').status_code, 403)

        stats = self.as_user(self.decision_maker).get('/api/assets/assets/stats/').json()
        self.assertEqual(stats['availability_rate'], 0)
        self.assertEqual(float(stats['maintenance_cost']), 1500.0)

    def test_dashboard_summary_is_scoped_to_the_user(self):
        self.create_incident()
        self.create_incident(reporter=self.other_citizen, status='resolved')

        citizen_view = self.as_user(self.citizen).get('/api/reports/reports/dashboard_summary/').json()
        self.assertEqual(citizen_view['incidents']['total'], 1)
        self.assertNotIn('users', citizen_view)
        self.assertEqual(len(citizen_view['incidents']['trend']), 30)

        manager_view = self.as_user(self.manager).get('/api/reports/reports/dashboard_summary/').json()
        self.assertEqual(manager_view['incidents']['total'], 2)
        self.assertEqual(manager_view['incidents']['resolution_rate'], 50.0)
        self.assertIn('users', manager_view)

    def test_reports_can_be_saved_by_managers_only(self):
        self.create_incident()
        today = timezone.localdate().isoformat()
        payload = {'start_date': today, 'end_date': today, 'save': True}

        refused = self.as_user(self.decision_maker).post('/api/reports/reports/generate_monthly_report/', payload, format='json')
        self.assertEqual(refused.status_code, 403)
        saved = self.as_user(self.manager).post('/api/reports/reports/generate_monthly_report/', payload, format='json')
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()['total_incidents'], 1)
        self.assertTrue(Report.objects.filter(pk=saved.json()['report_id']).exists())
        inverted = self.as_user(self.manager).post('/api/reports/reports/generate_monthly_report/', {
            'start_date': '2026-05-02', 'end_date': '2026-05-01',
        }, format='json')
        self.assertEqual(inverted.status_code, 400)

        snapshot = self.as_user(self.manager).post('/api/reports/reports/snapshot_kpi/')
        self.assertEqual(snapshot.status_code, 201)
        self.assertEqual(snapshot.json()['total_incidents'], 1)

    def test_notifications_can_all_be_marked_read(self):
        self.create_incident()
        api = self.as_user(self.manager)
        self.assertGreater(api.get('/api/notifications/unread_count/').json()['count'], 0)

        api.post('/api/notifications/mark_all_read/')

        self.assertEqual(api.get('/api/notifications/unread_count/').json()['count'], 0)
        self.assertFalse(Notification.objects.filter(recipient=self.manager, is_read=False).exists())


class PageTests(TestCase):
    @override_settings(SHOW_DEMO_ACCOUNTS=False)
    def test_login_page_hides_demo_accounts_unless_enabled(self):
        self.assertNotContains(self.client.get('/login/'), 'admin123')

    @override_settings(SHOW_DEMO_ACCOUNTS=True)
    def test_login_page_can_show_demo_accounts(self):
        self.assertContains(self.client.get('/login/'), 'admin123')

    @override_settings(TYPEBOT_ID='')
    def test_typebot_bubble_hidden_without_configuration(self):
        self.assertNotContains(self.client.get('/signaler/'), 'typebot-config')

    @override_settings(TYPEBOT_ID='giu-signalements', TYPEBOT_API_HOST='')
    def test_typebot_bubble_requires_self_hosted_viewer(self):
        self.assertNotContains(self.client.get('/signaler/'), 'typebot-config')

    @override_settings(TYPEBOT_ID='giu-signalements', TYPEBOT_API_HOST='https://bot.example.org')
    def test_typebot_bubble_shown_on_public_pages(self):
        for url in ['/', '/signaler/', '/suivi/']:
            response = self.client.get(url)
            self.assertContains(response, '"typebot": "giu-signalements"')
            self.assertContains(response, '"apiHost": "https://bot.example.org"')
