from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter


class PublicAPIRootRouter(DefaultRouter):
    """Router DRF dont la vue racine est accessible même avec des permissions globales strictes."""

    def get_api_root_view(self, api_urls=None):
        api_root_view = super().get_api_root_view(api_urls=api_urls)
        api_root_view.cls.permission_classes = [AllowAny]
        return api_root_view
