"""
URL configuration for urban_infrastructure project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve
from .views import (
    api_root,
    HomePageView,
    LoginPageView,
    DashboardPageView,
    PublicIncidentReportPageView,
    PublicIncidentTrackingPageView,
)
from urban_infrastructure.users.views import login_view, logout_view

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.svg', permanent=True)),
    path('login/', LoginPageView.as_view(), name='login'),
    path('login.html', LoginPageView.as_view(), name='login_html'),
    path('login/dashboard/', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('dashboard/', DashboardPageView.as_view(), name='dashboard'),
    path('signaler/', PublicIncidentReportPageView.as_view(), name='public_incident_report'),
    path('suivi/', PublicIncidentTrackingPageView.as_view(), name='public_incident_tracking'),
    path('api/', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/auth/login/', login_view, name='api_login'),
    path('api/auth/logout/', logout_view, name='api_logout'),
    path('api/auth/', include('rest_framework.urls')),
    
    # API endpoints
    path('api/users/', include('urban_infrastructure.users.urls')),
    path('api/incidents/', include('urban_infrastructure.incidents.urls')),
    path('api/assets/', include('urban_infrastructure.assets.urls')),
    path('api/interventions/', include('urban_infrastructure.interventions.urls')),
    path('api/reports/', include('urban_infrastructure.reports.urls')),
    path('api/notifications/', include('urban_infrastructure.notifications.urls')),
]

# `static()` ne sert les médias qu'en DEBUG : SERVE_MEDIA permet d'afficher les
# photos des signalements sur un hébergement sans stockage objet (démo Render).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(
            r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
