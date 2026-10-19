from django.db import transaction
from django.db.models import Count, Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import AssetType, Asset, AssetHistory
from .serializers import AssetTypeSerializer, AssetListSerializer, AssetDetailSerializer, AssetCreateSerializer, AssetHistorySerializer
from urban_infrastructure.users.permissions import CanManageIncidents, IsManagerOrAdmin


class AssetTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les types d'actifs"""
    queryset = AssetType.objects.all()
    serializer_class = AssetTypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class AssetViewSet(viewsets.ModelViewSet):
    """ViewSet pour les actifs"""
    queryset = Asset.objects.all()
    serializer_class = AssetListSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['code', 'name', 'location', 'brand', 'model']
    ordering_fields = ['code', 'name', 'installed_date', 'status', 'updated_at']
    ordering = ['code']

    def get_queryset(self):
        queryset = Asset.objects.select_related('asset_type')
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('history__performed_by')
        params = self.request.query_params
        if params.get('status'):
            queryset = queryset.filter(status__in=params['status'].split(','))
        if params.get('asset_type'):
            queryset = queryset.filter(asset_type_id=params['asset_type'])
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AssetCreateSerializer
        elif self.action == 'retrieve':
            return AssetDetailSerializer
        return AssetListSerializer

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        with transaction.atomic():
            asset = serializer.save()
            if asset.status != previous_status:
                AssetHistory.objects.create(
                    asset=asset,
                    action=AssetHistory.STATUS_CHANGE,
                    description=(
                        f'Statut : {dict(Asset.STATUS_CHOICES)[previous_status]} '
                        f'→ {asset.get_status_display()}'
                    ),
                    performed_by=self.request.user,
                )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Répartition du patrimoine par état et par type."""
        by_status = dict(Asset.objects.values_list('status').annotate(count=Count('id')))
        total = sum(by_status.values())
        return Response({
            'total': total,
            'availability_rate': round(
                by_status.get(Asset.OPERATIONAL, 0) / total * 100, 1,
            ) if total else 0,
            'by_status': [
                {'status': code, 'label': label, 'count': by_status.get(code, 0)}
                for code, label in Asset.STATUS_CHOICES
            ],
            'maintenance_cost': AssetHistory.objects.aggregate(total=Sum('cost'))['total'] or 0,
        })


class AssetHistoryViewSet(viewsets.ModelViewSet):
    """Journal d'entretien : consultation pour tous, saisie par les équipes terrain."""
    queryset = AssetHistory.objects.select_related('performed_by', 'asset')
    serializer_class = AssetHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('asset'):
            queryset = queryset.filter(asset_id=self.request.query_params['asset'])
        return queryset

    def get_permissions(self):
        if self.action == 'create':
            return [CanManageIncidents()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)
