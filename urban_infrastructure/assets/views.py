from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import AssetType, Asset, AssetHistory
from .serializers import AssetTypeSerializer, AssetListSerializer, AssetDetailSerializer, AssetCreateSerializer, AssetHistorySerializer


class AssetTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les types d'actifs"""
    queryset = AssetType.objects.all()
    serializer_class = AssetTypeSerializer
    permission_classes = [IsAuthenticated]


class AssetViewSet(viewsets.ModelViewSet):
    """ViewSet pour les actifs"""
    queryset = Asset.objects.all()
    serializer_class = AssetListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return AssetCreateSerializer
        elif self.action == 'retrieve':
            return AssetDetailSerializer
        return AssetListSerializer


class AssetHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour l'historique des actifs"""
    queryset = AssetHistory.objects.all()
    serializer_class = AssetHistorySerializer
    permission_classes = [IsAuthenticated]
