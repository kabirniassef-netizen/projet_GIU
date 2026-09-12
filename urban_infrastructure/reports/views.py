from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Count, Q, Avg, Sum
from datetime import datetime, timedelta
from .models import KPIMetrics, Report
from .serializers import KPIMetricsSerializer, ReportSerializer
from urban_infrastructure.incidents.models import Incident
from urban_infrastructure.interventions.models import Intervention
from urban_infrastructure.assets.models import Asset
from urban_infrastructure.users.permissions import CanConsultReports, IsManagerOrAdmin


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
    
    @action(detail=False, methods=['post'])
    def generate_monthly_report(self, request):
        """Générer un rapport mensuel"""
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date required'}, status=400)
        
        incidents_count = Incident.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).count()
        
        resolved_count = Incident.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status=Incident.RESOLVED
        ).count()
        
        report_data = {
            'period': f"{start_date} to {end_date}",
            'total_incidents': incidents_count,
            'resolved_incidents': resolved_count,
            'resolution_rate': (resolved_count / incidents_count * 100) if incidents_count > 0 else 0,
        }
        
        return Response(report_data)
