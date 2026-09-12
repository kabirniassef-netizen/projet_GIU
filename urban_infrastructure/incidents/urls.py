from django.urls import path, include
from urban_infrastructure.router import PublicAPIRootRouter
from .views import IncidentCategoryViewSet, IncidentViewSet

router = PublicAPIRootRouter()
router.register(r'categories', IncidentCategoryViewSet)
router.register(r'incidents', IncidentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
