from django.db import models
from django.contrib.auth import get_user_model
from urban_infrastructure.incidents.models import Incident
from urban_infrastructure.interventions.models import Intervention

User = get_user_model()


class KPIMetrics(models.Model):
    """Métriques clés de performance (KPI)"""
    date = models.DateField(auto_now_add=True)
    
    # Incidents metrics
    total_incidents = models.IntegerField(default=0)
    resolved_incidents = models.IntegerField(default=0)
    pending_incidents = models.IntegerField(default=0)
    avg_resolution_time = models.FloatField(default=0.0, help_text='En heures')
    
    # Interventions metrics
    completed_interventions = models.IntegerField(default=0)
    avg_intervention_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Asset metrics
    asset_availability = models.FloatField(default=0.0, help_text='En pourcentage')
    
    class Meta:
        verbose_name_plural = "KPI Metrics"
        ordering = ['-date']
    
    def __str__(self):
        return f"KPI Metrics - {self.date}"


class Report(models.Model):
    """Rapports générés"""
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    ANNUAL = 'annual'
    CUSTOM = 'custom'
    
    REPORT_TYPE_CHOICES = [
        (MONTHLY, 'Mensuel'),
        (QUARTERLY, 'Trimestriel'),
        (ANNUAL, 'Annuel'),
        (CUSTOM, 'Personnalisé'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Data
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Content (JSON or file)
    content = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"
