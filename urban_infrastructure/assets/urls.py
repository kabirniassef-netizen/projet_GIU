from django.urls import path, include
from urban_infrastructure.router import PublicAPIRootRouter
from .views import AssetTypeViewSet, AssetViewSet, AssetHistoryViewSet

router = PublicAPIRootRouter()
router.register(r'types', AssetTypeViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'history', AssetHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
