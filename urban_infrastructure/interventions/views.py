from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from urban_infrastructure.incidents.models import Incident, IncidentUpdate
from .models import Intervention, InterventionUpdate
from .serializers import (
    InterventionCreateSerializer,
    InterventionDetailSerializer,
    InterventionListSerializer,
    InterventionManageSerializer,
)
from urban_infrastructure.users.permissions import (
    CanUpdateInterventionStatus,
    IsManagerOrAdmin,
    effective_role,
)


def intervention_queryset():
    return Intervention.objects.select_related('incident', 'assigned_to')


class InterventionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les interventions"""
    queryset = Intervention.objects.all()
    serializer_class = InterventionListSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['incident__title', 'incident__commune', 'notes', 'assigned_to__username']
    ordering_fields = ['scheduled_date', 'created_at', 'priority', 'status']
    ordering = ['-scheduled_date']

    def get_queryset(self):
        user = self.request.user
        role = effective_role(user)
        if role == 'agent':
            queryset = intervention_queryset().filter(assigned_to=user)
        elif role in {'manager', 'admin'}:
            queryset = intervention_queryset()
        else:
            return Intervention.objects.none()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('updates__updated_by')

        params = self.request.query_params
        statuses = [value for value in params.get('status', '').split(',') if value]
        if statuses:
            queryset = queryset.filter(status__in=statuses)
        if params.get('assigned_to'):
            queryset = queryset.filter(assigned_to_id=params['assigned_to'])
        if params.get('date_from'):
            queryset = queryset.filter(scheduled_date__date__gte=params['date_from'])
        if params.get('date_to'):
            queryset = queryset.filter(scheduled_date__date__lte=params['date_to'])
        if params.get('active') == 'true':
            queryset = queryset.filter(status__in=Intervention.ACTIVE_STATUSES)
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        if self.action == 'update_status':
            return [CanUpdateInterventionStatus()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return InterventionCreateSerializer
        if self.action in ['update', 'partial_update']:
            return InterventionManageSerializer
        if self.action == 'retrieve':
            return InterventionDetailSerializer
        return InterventionListSerializer

    def perform_create(self, serializer):
        status_value = (
            Intervention.ASSIGNED
            if serializer.validated_data.get('assigned_to')
            else Intervention.PENDING
        )
        with transaction.atomic():
            intervention = serializer.save(status=status_value)
            InterventionUpdate.objects.create(
                intervention=intervention,
                status=status_value,
                comment='Intervention planifiée.',
                updated_by=self.request.user,
            )
            incident = intervention.incident
            incident.status = Incident.PLANNED
            incident.save()
            IncidentUpdate.objects.create(
                incident=incident,
                status=Incident.PLANNED,
                comment='Intervention planifiée.',
                updated_by=self.request.user,
            )

    def perform_update(self, serializer):
        previous_agent_id = serializer.instance.assigned_to_id
        with transaction.atomic():
            intervention = serializer.save()
            if intervention.assigned_to_id and intervention.status == Intervention.PENDING:
                intervention.status = Intervention.ASSIGNED
                intervention.save()
            if intervention.assigned_to_id != previous_agent_id:
                agent = intervention.assigned_to
                InterventionUpdate.objects.create(
                    intervention=intervention,
                    status=intervention.status,
                    comment=(
                        f'Réaffectée à {agent.get_full_name() or agent.username}.'
                        if agent else 'Agent retiré.'
                    ),
                    updated_by=self.request.user,
                )

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        intervention = intervention_queryset().prefetch_related('updates__updated_by').get(
            pk=kwargs['pk'],
        )
        return Response(InterventionDetailSerializer(intervention, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'une intervention (photo de compte rendu facultative)."""
        intervention = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')

        if new_status not in dict(Intervention.STATUS_CHOICES):
            return Response(
                {'error': 'Status invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if effective_role(request.user) == 'agent' and new_status not in {
            Intervention.IN_PROGRESS, Intervention.COMPLETED,
        }:
            return Response(
                {'error': 'Les agents ne peuvent que prendre en charge ou terminer une intervention.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not intervention.can_transition_to(new_status):
            return Response(
                {'error': 'Transition de statut invalide.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            intervention.status = new_status
            if new_status == Intervention.COMPLETED:
                intervention.completed_date = timezone.now()
            intervention.save()

            update_data = {
                'intervention': intervention,
                'status': new_status,
                'comment': comment,
                'updated_by': request.user,
            }
            if 'photo' in request.FILES:
                update_data['photo'] = request.FILES['photo']
            InterventionUpdate.objects.create(**update_data)

            incident = intervention.incident
            incident_status = {
                Intervention.IN_PROGRESS: Incident.IN_PROGRESS,
                Intervention.COMPLETED: Incident.RESOLVED,
            }.get(new_status)
            if incident_status and incident.status != incident_status:
                incident.status = incident_status
                incident.save()
                IncidentUpdate.objects.create(
                    incident=incident,
                    status=incident_status,
                    comment=comment,
                    updated_by=request.user,
                )
            elif new_status == Intervention.CANCELLED and incident.status in (
                Incident.REOPEN_TRANSITIONS
            ):
                incident.reopen_for_planning()
                IncidentUpdate.objects.create(
                    incident=incident,
                    status=Incident.VALIDATED,
                    comment=comment or 'Intervention annulée : incident à replanifier.',
                    updated_by=request.user,
                )

        intervention = intervention_queryset().prefetch_related('updates__updated_by').get(
            pk=intervention.pk,
        )
        return Response(InterventionDetailSerializer(intervention, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def my_interventions(self, request):
        """Récupérer les interventions assignées à l'utilisateur"""
        interventions = intervention_queryset().filter(assigned_to=request.user)
        serializer = self.get_serializer(interventions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Filtrer les interventions par statut"""
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)
