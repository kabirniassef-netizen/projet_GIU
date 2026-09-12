from django.urls import path, include
from urban_infrastructure.router import PublicAPIRootRouter
from .views import CustomUserViewSet, UserRoleViewSet

router = PublicAPIRootRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'roles', UserRoleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
