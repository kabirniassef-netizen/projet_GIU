from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, UserRoleViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'roles', UserRoleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
