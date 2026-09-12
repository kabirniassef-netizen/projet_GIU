from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import IncidentCategory, Incident, IncidentUpdate
from .serializers import (
    IncidentCategorySerializer, IncidentListSerializer, IncidentDetailSerializer,
    IncidentCreateSerializer, IncidentUpdateSerializer
)
from urban_infrastructure.users.permissions import CanManageIncidents, IsManagerOrAdmin


class IncidentCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les catégories d'incidents"""
    queryset = IncidentCategory.objects.all()
    serializer_class = IncidentCategorySerializer
    permission_classes = [IsAuthenticated]


class IncidentViewSet(viewsets.ModelViewSet):
    """ViewSet pour les incidents"""
    queryset = Incident.objects.all()
    serializer_class = IncidentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'citizen' and not self.request.user.is_superuser:
            return Incident.objects.filter(reporter=self.request.user)
        return Incident.objects.all()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        if self.action == 'update_status':
            return [CanManageIncidents()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return IncidentCreateSerializer
        elif self.action == 'retrieve':
            return IncidentDetailSerializer
        return IncidentListSerializer
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'un incident"""
        incident = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        if new_status not in dict(Incident.STATUS_CHOICES):
            return Response(
                {'error': 'Status invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        incident.status = new_status
        incident.save()
        
        # Créer une mise à jour
        IncidentUpdate.objects.create(
            incident=incident,
            status=new_status,
            comment=comment,
            updated_by=request.user
        )
        
        return Response(IncidentDetailSerializer(incident).data)
    
    @action(detail=False, methods=['get'])
    def my_incidents(self, request):
        """Récupérer les incidents de l'utilisateur connecté"""
        incidents = Incident.objects.filter(reporter=request.user)
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Filtrer les incidents par statut"""
        status_filter = request.query_params.get('status')
        if status_filter:
            incidents = self.get_queryset().filter(status=status_filter)
        else:
            incidents = self.get_queryset()
        
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)
