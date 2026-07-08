from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
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
            'users': {
                'list_users': 'GET /api/users/users/',
                'create_user': 'POST /api/users/users/',
                'current_user': 'GET /api/users/users/me/',
                'user_roles': 'GET /api/users/roles/',
            },
            'incidents': {
                'list_incidents': 'GET /api/incidents/incidents/',
                'create_incident': 'POST /api/incidents/incidents/',
                'my_incidents': 'GET /api/incidents/incidents/my_incidents/',
                'update_status': 'POST /api/incidents/incidents/{id}/update_status/',
            },
            'assets': {
                'list_assets': 'GET /api/assets/assets/',
                'create_asset': 'POST /api/assets/assets/',
                'asset_types': 'GET /api/assets/types/',
            },
            'interventions': {
                'list_interventions': 'GET /api/interventions/interventions/',
                'create_intervention': 'POST /api/interventions/interventions/',
                'my_interventions': 'GET /api/interventions/interventions/my_interventions/',
            },
            'reports': {
                'global_statistics': 'GET /api/reports/reports/global_statistics/',
                'incidents_by_status': 'GET /api/reports/reports/incidents_by_status/',
                'kpi_summary': 'GET /api/reports/reports/kpi_summary/',
            }
        }
    })


class HomePageView(TemplateView):
    """Vue pour la page d'accueil"""
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Système de Gestion d\'Infrastructure Urbaine'
        return context


class LoginPageView(TemplateView):
    """Vue pour afficher la page de connexion"""
    template_name = 'login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Connexion - GIU'
        return context
