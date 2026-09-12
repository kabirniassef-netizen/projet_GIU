from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Intervention, InterventionUpdate
from .serializers import InterventionListSerializer, InterventionDetailSerializer, InterventionCreateSerializer, InterventionUpdateSerializer
from urban_infrastructure.users.permissions import IsManagerOrAdmin


class InterventionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les interventions"""
    queryset = Intervention.objects.all()
    serializer_class = InterventionListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'citizen' and not user.is_superuser:
            return Intervention.objects.none()
        if user.role == 'agent' and not user.is_superuser:
            return Intervention.objects.filter(assigned_to=user)
        return Intervention.objects.all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return InterventionCreateSerializer
        elif self.action == 'retrieve':
            return InterventionDetailSerializer
        return InterventionListSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'une intervention"""
        intervention = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        if new_status not in dict(Intervention.STATUS_CHOICES):
            return Response(
                {'error': 'Status invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        intervention.status = new_status
        if new_status == Intervention.COMPLETED:
            intervention.completed_date = timezone.now()
        intervention.save()
        
        # Créer une mise à jour
        update_data = {
            'intervention': intervention,
            'status': new_status,
            'comment': comment,
            'updated_by': request.user
        }
        
        if 'photo' in request.FILES:
            update_data['photo'] = request.FILES['photo']
        
        InterventionUpdate.objects.create(**update_data)
        
        return Response(InterventionDetailSerializer(intervention).data)
    
    @action(detail=False, methods=['get'])
    def my_interventions(self, request):
        """Récupérer les interventions assignées à l'utilisateur"""
        interventions = Intervention.objects.filter(assigned_to=request.user)
        serializer = self.get_serializer(interventions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Filtrer les interventions par statut"""
        status_filter = request.query_params.get('status')
        if status_filter:
            interventions = self.get_queryset().filter(status=status_filter)
        else:
            interventions = self.get_queryset()
        
        serializer = self.get_serializer(interventions, many=True)
        return Response(serializer.data)


from django.utils import timezone
