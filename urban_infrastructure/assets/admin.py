from django.contrib import admin
from .models import AssetType, Asset, AssetHistory


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('code', 'asset_type', 'status', 'location', 'installed_date')
    list_filter = ('asset_type', 'status', 'installed_date')
    search_fields = ('code', 'name', 'location')
    readonly_fields = ('created_at', 'updated_at', 'latitude', 'longitude')
    fieldsets = (
        (None, {'fields': ('code', 'name', 'asset_type', 'description')}),
        ('Location', {'fields': ('latitude', 'longitude', 'location')}),
        ('Technical Info', {'fields': ('model', 'brand', 'specifications')}),
        ('Status', {'fields': ('status', 'installed_date')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(AssetHistory)
class AssetHistoryAdmin(admin.ModelAdmin):
    list_display = ('asset', 'action', 'date')
    list_filter = ('action', 'date')
    search_fields = ('asset__code', 'asset__name')
    readonly_fields = ('date',)
