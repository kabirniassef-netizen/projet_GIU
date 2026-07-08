from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterventionViewSet

router = DefaultRouter()
router.register(r'interventions', InterventionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
