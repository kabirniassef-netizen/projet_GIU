from django.contrib import admin
from .models import IncidentCategory, Incident, IncidentUpdate


@admin.register(IncidentCategory)
class IncidentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'reporter', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'description', 'reporter__username')
    readonly_fields = ('created_at', 'updated_at', 'address')
    fieldsets = (
        (None, {'fields': ('title', 'description', 'category', 'reporter')}),
        ('Location', {'fields': ('region', 'department', 'commune')}),
        ('Ancienne adresse (signalements historiques)', {'fields': ('address',)}),
        ('Status', {'fields': ('status', 'priority')}),
        ('Photo', {'fields': ('photo',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(IncidentUpdate)
class IncidentUpdateAdmin(admin.ModelAdmin):
    list_display = ('incident', 'status', 'updated_by', 'updated_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('incident__title', 'updated_by__username')
    readonly_fields = ('updated_at',)
