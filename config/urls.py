"""
URL configuration for urban_infrastructure project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from .views import api_root, HomePageView, LoginPageView, DashboardPageView
from urban_infrastructure.users.views import login_view
from urban_infrastructure.notifications.webhooks import whatsapp_webhook

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('login.html', LoginPageView.as_view(), name='login_html'),
    path('login/dashboard/', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('dashboard/', DashboardPageView.as_view(), name='dashboard'),
    path('api/', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/auth/login/', login_view, name='api_login'),
    path('api/auth/', include('rest_framework.urls')),
    path('webhooks/whatsapp/', whatsapp_webhook, name='whatsapp_webhook'),
    
    # API endpoints
    path('api/users/', include('urban_infrastructure.users.urls')),
    path('api/incidents/', include('urban_infrastructure.incidents.urls')),
    path('api/assets/', include('urban_infrastructure.assets.urls')),
    path('api/interventions/', include('urban_infrastructure.interventions.urls')),
    path('api/reports/', include('urban_infrastructure.reports.urls')),
    path('api/notifications/', include('urban_infrastructure.notifications.urls')),
]

# Serve uploaded media from the persistent Render disk.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
