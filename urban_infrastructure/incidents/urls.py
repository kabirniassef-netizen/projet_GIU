from django.urls import path, include
from urban_infrastructure.router import PublicAPIRootRouter
from .views import (
    IncidentCategoryViewSet,
    IncidentViewSet,
    PublicIncidentCreateView,
    PublicIncidentTrackingView,
)

router = PublicAPIRootRouter()
router.register(r'categories', IncidentCategoryViewSet)
router.register(r'incidents', IncidentViewSet)

urlpatterns = [
    path('public/', PublicIncidentCreateView.as_view(), name='public-incident-create'),
    path(
        'track/<str:tracking_code>/',
        PublicIncidentTrackingView.as_view(),
        name='public-incident-track',
    ),
    path('', include(router.urls)),
]
