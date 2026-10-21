import csv

from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from .models import IncidentCategory, Incident, IncidentUpdate
from .serializers import (
    IncidentCategorySerializer, IncidentListSerializer, IncidentDetailSerializer,
    IncidentCreateSerializer, IncidentManageSerializer,
    PublicIncidentCreateSerializer, PublicIncidentTrackingSerializer,
)
from urban_infrastructure.interventions.models import Intervention
from urban_infrastructure.users.permissions import (
    CanManageIncidents,
    CanReportIncident,
    IsManagerOrAdmin,
    REPORTING_ROLES,
    effective_role,
    has_role,
)


def incident_queryset():
    return Incident.objects.select_related('category', 'reporter').prefetch_related(
        Prefetch(
            'interventions',
            queryset=Intervention.objects.select_related('assigned_to'),
        ),
    )


def filter_incidents(queryset, params):
    """Filtres communs à la liste et à l'export : statut, catégorie, priorité, dates."""
    statuses = [value for value in params.get('status', '').split(',') if value]
    if statuses:
        queryset = queryset.filter(status__in=statuses)
    priorities = [value for value in params.get('priority', '').split(',') if value]
    if priorities:
        queryset = queryset.filter(priority__in=priorities)
    if params.get('category'):
        queryset = queryset.filter(category_id=params['category'])
    if params.get('reporter'):
        queryset = queryset.filter(reporter_id=params['reporter'])
    if params.get('commune'):
        queryset = queryset.filter(commune__icontains=params['commune'])
    if params.get('date_from'):
        queryset = queryset.filter(created_at__date__gte=params['date_from'])
    if params.get('date_to'):
        queryset = queryset.filter(created_at__date__lte=params['date_to'])
    if params.get('unplanned') == 'true':
        queryset = queryset.filter(status=Incident.VALIDATED)
    return queryset


class IncidentCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les catégories d'incidents"""
    queryset = IncidentCategory.objects.order_by('id')
    serializer_class = IncidentCategorySerializer
    permission_classes = [AllowAny]


class PublicIncidentCreateView(APIView):
    """Permet aux citoyens de signaler un incident sans créer de compte."""
    # Formulaire anonyme : une session ouverte dans le navigateur ne doit pas
    # imposer le jeton CSRF que la page publique n'envoie pas.
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = PublicIncidentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incident = serializer.save(reporter=None)
        IncidentUpdate.objects.create(
            incident=incident,
            status=incident.status,
            comment='Signalement créé sans compte.',
        )
        return Response(
            IncidentDetailSerializer(incident, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class PublicIncidentTrackingView(APIView):
    """Suivi d'un signalement à partir de son code, sans authentification."""
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def get(self, request, tracking_code):
        incident = get_object_or_404(
            Incident.objects.select_related('category').prefetch_related('updates'),
            tracking_code=tracking_code.strip().upper(),
        )
        return Response(PublicIncidentTrackingSerializer(incident).data)


class IncidentViewSet(viewsets.ModelViewSet):
    """ViewSet pour les incidents"""
    queryset = Incident.objects.all()
    serializer_class = IncidentListSerializer
    permission_classes = [IsAuthenticated]
    search_fields = [
        'title', 'description', 'address', 'commune', 'department', 'region',
        'tracking_code', 'reporter__username',
    ]
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        role = effective_role(user)
        queryset = incident_queryset()
        if role == 'citizen':
            queryset = queryset.filter(reporter=user)
        elif role == 'agent':
            queryset = queryset.filter(interventions__assigned_to=user).distinct()
        elif role not in {'manager', 'admin'}:
            return Incident.objects.none()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('updates__updated_by')
        return filter_incidents(queryset, self.request.query_params)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        if self.action in ['update_status', 'comment']:
            return [CanManageIncidents()]
        if self.action == 'create':
            return [CanReportIncident()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return IncidentCreateSerializer
        if self.action in ['update', 'partial_update']:
            return IncidentManageSerializer
        if self.action == 'retrieve':
            return IncidentDetailSerializer
        return IncidentListSerializer

    def perform_create(self, serializer):
        incident = serializer.save(reporter=self.request.user)
        IncidentUpdate.objects.create(
            incident=incident,
            status=incident.status,
            comment='Signalement créé.',
            updated_by=self.request.user,
        )

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        incident = incident_queryset().prefetch_related('updates__updated_by').get(
            pk=kwargs['pk'],
        )
        return Response(IncidentDetailSerializer(incident, context={'request': request}).data)

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

        if effective_role(request.user) == 'agent' and new_status not in {
            Incident.IN_PROGRESS, Incident.RESOLVED,
        }:
            return Response(
                {'error': 'Les agents ne peuvent que prendre en charge ou résoudre un incident.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not incident.can_transition_to(new_status):
            return Response(
                {'error': 'Transition de statut invalide.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            incident.status = new_status
            incident.save()
            IncidentUpdate.objects.create(
                incident=incident,
                status=new_status,
                comment=comment,
                updated_by=request.user
            )
        incident = incident_queryset().prefetch_related('updates__updated_by').get(pk=incident.pk)
        return Response(IncidentDetailSerializer(incident, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """Ajouter une note de suivi sans changer le statut."""
        incident = self.get_object()
        text = (request.data.get('comment') or '').strip()
        if not text:
            return Response(
                {'comment': ['Le commentaire ne peut pas être vide.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        IncidentUpdate.objects.create(
            incident=incident,
            status=incident.status,
            comment=text[:2000],
            updated_by=request.user,
        )
        incident = incident_queryset().prefetch_related('updates__updated_by').get(pk=incident.pk)
        return Response(IncidentDetailSerializer(incident, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def my_incidents(self, request):
        """Récupérer les incidents de l'utilisateur connecté"""
        incidents = incident_queryset().filter(reporter=request.user)
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Filtrer les incidents par statut"""
        incidents = self.get_queryset()
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export CSV (Excel) des incidents visibles, avec les filtres appliqués."""
        if not has_role(request.user, REPORTING_ROLES):
            return Response(status=status.HTTP_403_FORBIDDEN)
        queryset = self.filter_queryset(
            filter_incidents(incident_queryset(), request.query_params)
        )
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f'incidents-{timezone.localdate():%Y%m%d}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('﻿')  # BOM pour un affichage correct des accents dans Excel
        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'Référence', 'Code de suivi', 'Titre', 'Catégorie', 'Priorité', 'Statut',
            'Région', 'Département', 'Commune', 'Adresse', 'Signalé par', 'Créé le',
            'Mis à jour le',
        ])
        for incident in queryset:
            writer.writerow([
                incident.pk,
                incident.tracking_code,
                incident.title,
                incident.category.get_name_display(),
                incident.get_priority_display(),
                incident.get_status_display(),
                incident.region,
                incident.department,
                incident.commune,
                incident.address,
                incident.reporter.username if incident.reporter else 'Anonyme',
                timezone.localtime(incident.created_at).strftime('%d/%m/%Y %H:%M'),
                timezone.localtime(incident.updated_at).strftime('%d/%m/%Y %H:%M'),
            ])
        return response
