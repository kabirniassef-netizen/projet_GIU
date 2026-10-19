from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from .analytics import (
    asset_summary,
    average_resolution_hours,
    incident_summary,
    intervention_summary,
)
from .models import KPIMetrics, Report
from .serializers import KPIMetricsSerializer, ReportSerializer
from urban_infrastructure.incidents.models import Incident
from urban_infrastructure.interventions.models import Intervention
from urban_infrastructure.assets.models import Asset
from urban_infrastructure.assets.models import AssetHistory
from urban_infrastructure.users.models import CustomUser
from urban_infrastructure.users.permissions import (
    CanConsultReports,
    IsManagerOrAdmin,
    effective_role,
)


class KPIMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les métriques KPI"""
    queryset = KPIMetrics.objects.all()
    serializer_class = KPIMetricsSerializer
    permission_classes = [CanConsultReports]
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Récupérer les dernières métriques KPI"""
        latest_kpi = KPIMetrics.objects.first()
        if latest_kpi:
            serializer = self.get_serializer(latest_kpi)
            return Response(serializer.data)
        return Response({'error': 'No KPI data available'}, status=404)
    
    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Récupérer les métriques KPI pour une plage de dates"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = KPIMetrics.objects.all()
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet pour les rapports"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsManagerOrAdmin]

    def get_permissions(self):
        if self.action == 'global_statistics':
            return [AllowAny()]
        if self.action == 'dashboard_summary':
            return [IsAuthenticated()]
        if self.action in [
            'list', 'retrieve', 'generate_dashboard', 'generate_monthly_report',
        ]:
            return [CanConsultReports()]
        return [IsManagerOrAdmin()]
    
    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def global_statistics(self, request):
        """Indicateurs publics affichés sur la page d'accueil."""
        total_assets = Asset.objects.count()
        operational_assets = Asset.objects.filter(status=Asset.OPERATIONAL).count()
        total_interventions = Intervention.objects.count()
        completed_interventions = Intervention.objects.filter(
            status=Intervention.COMPLETED
        ).count()

        return Response({
            'total_incidents': Incident.objects.count(),
            'resolved_incidents': Incident.objects.filter(
                status=Incident.RESOLVED
            ).count(),
            'total_interventions': total_interventions,
            'completed_interventions': completed_interventions,
            'asset_availability_rate': round(
                (operational_assets / total_assets * 100) if total_assets else 0,
                1,
            ),
        })
    
    @action(detail=False, methods=['post'])
    def generate_dashboard(self, request):
        """Générer les données du tableau de bord"""
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # Incidents statistics
        total_incidents = Incident.objects.count()
        resolved_incidents = Incident.objects.filter(status=Incident.RESOLVED).count()
        incidents_this_month = Incident.objects.filter(created_at__date__gte=thirty_days_ago).count()
        
        # Interventions statistics
        completed_interventions = Intervention.objects.filter(status=Intervention.COMPLETED).count()
        pending_interventions = Intervention.objects.filter(status=Intervention.PENDING).count()
        
        # Category distribution
        category_dist = Incident.objects.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Priority distribution
        priority_dist = Incident.objects.values('priority').annotate(
            count=Count('id')
        ).order_by('-count')
        
        dashboard_data = {
            'total_incidents': total_incidents,
            'resolved_incidents': resolved_incidents,
            'incidents_this_month': incidents_this_month,
            'completed_interventions': completed_interventions,
            'pending_interventions': pending_interventions,
            'category_distribution': list(category_dist),
            'priority_distribution': list(priority_dist),
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Indicateurs du tableau de bord, limités au périmètre de l'utilisateur."""
        user = request.user
        role = effective_role(user)
        incidents = Incident.objects.all()
        interventions = Intervention.objects.all()
        if role == 'citizen':
            incidents = incidents.filter(reporter=user)
            interventions = interventions.none()
        elif role == 'agent':
            interventions = interventions.filter(assigned_to=user)
            incidents = incidents.filter(interventions__assigned_to=user).distinct()

        data = {
            'scope': role,
            'incidents': incident_summary(incidents),
            'interventions': intervention_summary(interventions),
            'assets': asset_summary(),
        }
        if role in {'manager', 'admin'}:
            data['users'] = {
                'total': CustomUser.objects.count(),
                'citizens': CustomUser.objects.filter(role='citizen').count(),
                'agents': CustomUser.objects.filter(role='agent', is_active=True).count(),
            }
        return Response(data)

    @action(detail=False, methods=['post'])
    def generate_monthly_report(self, request):
        """Générer un rapport sur une période ; `save=true` l'enregistre."""
        start_date = parse_date(str(request.data.get('start_date') or ''))
        end_date = parse_date(str(request.data.get('end_date') or ''))
        
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date required'}, status=400)
        if start_date > end_date:
            return Response(
                {'error': 'La date de début doit précéder la date de fin.'},
                status=400,
            )

        incidents = Incident.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        incidents_count = incidents.count()
        resolved_count = incidents.filter(status=Incident.RESOLVED).count()
        interventions = Intervention.objects.filter(
            scheduled_date__date__gte=start_date,
            scheduled_date__date__lte=end_date,
        )
        summary = incident_summary(incidents, days=min((end_date - start_date).days + 1, 92))

        report_data = {
            'period': f"{start_date} to {end_date}",
            'total_incidents': incidents_count,
            'resolved_incidents': resolved_count,
            'resolution_rate': (resolved_count / incidents_count * 100) if incidents_count > 0 else 0,
            'avg_resolution_hours': average_resolution_hours(incidents),
            'rejected_incidents': incidents.filter(status=Incident.REJECTED).count(),
            'by_category': summary['by_category'],
            'by_priority': summary['by_priority'],
            'interventions_planned': interventions.count(),
            'interventions_completed': interventions.filter(
                status=Intervention.COMPLETED,
            ).count(),
            'maintenance_cost': float(AssetHistory.objects.filter(
                date__date__gte=start_date,
                date__date__lte=end_date,
            ).aggregate(total=Sum('cost'))['total'] or 0),
        }

        if str(request.data.get('save', '')).lower() in {'1', 'true', 'yes'}:
            if effective_role(request.user) not in {'manager', 'admin'}:
                return Response(
                    {'error': 'Seuls les gestionnaires peuvent enregistrer un rapport.'},
                    status=403,
                )
            days = (end_date - start_date).days + 1
            report_type = (
                Report.MONTHLY if days <= 31 else
                Report.QUARTERLY if days <= 92 else
                Report.ANNUAL if days >= 365 else Report.CUSTOM
            )
            report = Report.objects.create(
                title=request.data.get('title') or f'Rapport du {start_date:%d/%m/%Y} au {end_date:%d/%m/%Y}',
                report_type=report_type,
                generated_by=request.user,
                start_date=start_date,
                end_date=end_date,
                content=report_data,
            )
            report_data['report_id'] = report.pk
        
        return Response(report_data)

    @action(detail=False, methods=['post'])
    def snapshot_kpi(self, request):
        """Enregistre un instantané des KPI du jour (historisation)."""
        incidents = Incident.objects.all()
        summary = incident_summary(incidents)
        cost = AssetHistory.objects.aggregate(avg=Avg('cost'))['avg'] or 0
        metric = KPIMetrics.objects.create(
            total_incidents=summary['total'],
            resolved_incidents=summary['resolved'],
            pending_incidents=summary['open'],
            avg_resolution_time=summary['avg_resolution_hours'] or 0,
            completed_interventions=Intervention.objects.filter(
                status=Intervention.COMPLETED,
            ).count(),
            avg_intervention_cost=round(cost, 2),
            asset_availability=asset_summary()['availability_rate'],
        )
        return Response(KPIMetricsSerializer(metric).data, status=201)
