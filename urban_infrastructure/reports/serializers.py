from rest_framework import serializers
from .models import KPIMetrics, Report


class KPIMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIMetrics
        fields = [
            'id', 'date', 'total_incidents', 'resolved_incidents', 'pending_incidents',
            'avg_resolution_time', 'completed_interventions', 'avg_intervention_cost',
            'asset_availability'
        ]


class ReportSerializer(serializers.ModelSerializer):
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'report_type', 'report_type_display', 'description',
            'generated_by', 'generated_by_username', 'start_date', 'end_date',
            'content', 'created_at'
        ]
