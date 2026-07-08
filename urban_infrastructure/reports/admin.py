from django.contrib import admin
from .models import KPIMetrics, Report


@admin.register(KPIMetrics)
class KPIMetricsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_incidents', 'resolved_incidents', 'asset_availability')
    list_filter = ('date',)
    readonly_fields = ('date',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'generated_by', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'generated_by__username')
    readonly_fields = ('created_at',)
