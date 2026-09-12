from django.urls import path, include
from urban_infrastructure.router import PublicAPIRootRouter
from .views import KPIMetricsViewSet, ReportViewSet

router = PublicAPIRootRouter()
router.register(r'metrics', KPIMetricsViewSet)
router.register(r'reports', ReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
