from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API Root - Liste des endpoints disponibles"""
    return Response({
        'message': 'Bienvenue sur le système de gestion d\'infrastructure urbaine',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api_auth': '/api/auth/',
            'users': '/api/users/',
            'incidents': '/api/incidents/',
            'assets': '/api/assets/',
            'interventions': '/api/interventions/',
            'reports': '/api/reports/',
        },
        'documentation': {
            'auth': {
                'login': 'POST /api/auth/login/',
                'logout': 'POST /api/auth/logout/',
            },
            'users': {
                'list_users': 'GET /api/users/users/?search=&role=&is_active=',
                'create_user': 'POST /api/users/users/',
                'current_user': 'GET|PATCH /api/users/users/me/',
                'change_password': 'POST /api/users/users/change_password/',
                'toggle_active': 'POST /api/users/users/{id}/toggle_active/',
                'reset_password': 'POST /api/users/users/{id}/reset_password/',
                'user_stats': 'GET /api/users/users/stats/',
                'user_roles': 'GET /api/users/roles/',
            },
            'incidents': {
                'list_incidents': 'GET /api/incidents/incidents/?search=&status=&priority=&category=',
                'create_incident': 'POST /api/incidents/incidents/',
                'public_report': 'POST /api/incidents/public/',
                'public_tracking': 'GET /api/incidents/track/{tracking_code}/',
                'my_incidents': 'GET /api/incidents/incidents/my_incidents/',
                'update_status': 'POST /api/incidents/incidents/{id}/update_status/',
                'comment': 'POST /api/incidents/incidents/{id}/comment/',
                'export_csv': 'GET /api/incidents/incidents/export/',
            },
            'assets': {
                'list_assets': 'GET /api/assets/assets/?search=&status=&asset_type=',
                'create_asset': 'POST /api/assets/assets/',
                'asset_stats': 'GET /api/assets/assets/stats/',
                'asset_types': 'GET /api/assets/types/',
                'maintenance_log': 'GET|POST /api/assets/history/',
            },
            'interventions': {
                'list_interventions': 'GET /api/interventions/interventions/?status=&active=true',
                'create_intervention': 'POST /api/interventions/interventions/',
                'reassign': 'PATCH /api/interventions/interventions/{id}/',
                'update_status': 'POST /api/interventions/interventions/{id}/update_status/',
                'my_interventions': 'GET /api/interventions/interventions/my_interventions/',
            },
            'reports': {
                'global_statistics': 'GET /api/reports/reports/global_statistics/',
                'dashboard_summary': 'GET /api/reports/reports/dashboard_summary/',
                'generate_report': 'POST /api/reports/reports/generate_monthly_report/',
                'snapshot_kpi': 'POST /api/reports/reports/snapshot_kpi/',
            },
            'notifications': {
                'list': 'GET /api/notifications/',
                'unread_count': 'GET /api/notifications/unread_count/',
                'mark_all_read': 'POST /api/notifications/mark_all_read/',
            }
        }
    })


class HomePageView(TemplateView):
    """Vue pour la page d'accueil"""
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Système de Gestion d\'Infrastructure Urbaine'
        context['citizen_only'] = settings.CITIZEN_HOME_ONLY
        return context


class LoginPageView(TemplateView):
    """Vue pour afficher la page de connexion"""
    template_name = 'login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Connexion - GIU'
        context['show_demo_accounts'] = settings.SHOW_DEMO_ACCOUNTS
        return context


class PublicIncidentReportPageView(TemplateView):
    """Formulaire de signalement accessible sans authentification."""
    template_name = 'report_incident.html'


class PublicIncidentTrackingPageView(TemplateView):
    """Suivi public d'un signalement grâce à son code."""
    template_name = 'track_incident.html'


class DashboardPageView(TemplateView):
    """Espace de travail après authentification."""
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        if request.GET.get('signalement') == '1':
            return redirect('public_incident_report')
        return super().get(request, *args, **kwargs)
