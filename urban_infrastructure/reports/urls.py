from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KPIMetricsViewSet, ReportViewSet

router = DefaultRouter()
router.register(r'metrics', KPIMetricsViewSet)
router.register(r'reports', ReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
