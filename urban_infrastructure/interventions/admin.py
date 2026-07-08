from django.contrib import admin
from .models import Intervention, InterventionUpdate


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident', 'assigned_to', 'status', 'priority', 'scheduled_date')
    list_filter = ('status', 'priority', 'scheduled_date')
    search_fields = ('incident__title', 'assigned_to__username')
    readonly_fields = ('created_at', 'completed_date')
    fieldsets = (
        (None, {'fields': ('incident', 'assigned_to')}),
        ('Planning', {'fields': ('scheduled_date', 'estimated_duration')}),
        ('Status', {'fields': ('status', 'priority', 'completed_date')}),
        ('Details', {'fields': ('notes',)}),
        ('Dates', {'fields': ('created_at',)}),
    )


@admin.register(InterventionUpdate)
class InterventionUpdateAdmin(admin.ModelAdmin):
    list_display = ('intervention', 'status', 'updated_by', 'updated_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('intervention__incident__title', 'updated_by__username')
    readonly_fields = ('updated_at',)
