"""
URL configuration for urban_infrastructure project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import api_root, HomePageView, LoginPageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('login.html', LoginPageView.as_view(), name='login_html'),
    path('api/', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('rest_framework.urls')),
    
    # API endpoints
    path('api/users/', include('urban_infrastructure.users.urls')),
    path('api/incidents/', include('urban_infrastructure.incidents.urls')),
    path('api/assets/', include('urban_infrastructure.assets.urls')),
    path('api/interventions/', include('urban_infrastructure.interventions.urls')),
    path('api/reports/', include('urban_infrastructure.reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
