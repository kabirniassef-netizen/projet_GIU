from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncidentCategoryViewSet, IncidentViewSet

router = DefaultRouter()
router.register(r'categories', IncidentCategoryViewSet)
router.register(r'incidents', IncidentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
