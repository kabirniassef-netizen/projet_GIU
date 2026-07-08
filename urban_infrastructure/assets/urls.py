from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetTypeViewSet, AssetViewSet, AssetHistoryViewSet

router = DefaultRouter()
router.register(r'types', AssetTypeViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'history', AssetHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
