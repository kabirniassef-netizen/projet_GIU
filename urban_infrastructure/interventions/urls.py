from django.urls import path, include
from urban_infrastructure.router import PublicAPIRootRouter
from .views import InterventionViewSet

router = PublicAPIRootRouter()
router.register(r'interventions', InterventionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
