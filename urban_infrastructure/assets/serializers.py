from rest_framework import serializers
from .models import AssetType, Asset, AssetHistory


class AssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetType
        fields = ['id', 'name', 'description']


class AssetHistorySerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)
    
    class Meta:
        model = AssetHistory
        fields = ['id', 'action', 'action_display', 'description', 'cost', 'performed_by', 'performed_by_username', 'date']


class AssetListSerializer(serializers.ModelSerializer):
    asset_type_name = serializers.CharField(source='asset_type.get_name_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Asset
        fields = [
            'id', 'code', 'name', 'asset_type', 'asset_type_name', 'latitude', 'longitude',
            'location', 'status', 'status_display', 'installed_date'
        ]


class AssetDetailSerializer(serializers.ModelSerializer):
    asset_type_name = serializers.CharField(source='asset_type.get_name_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    history = AssetHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Asset
        fields = [
            'id', 'code', 'name', 'asset_type', 'asset_type_name', 'description',
            'latitude', 'longitude', 'location', 'model', 'brand', 'specifications',
            'status', 'status_display', 'installed_date', 'created_at', 'updated_at', 'history'
        ]


class AssetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['code', 'name', 'asset_type', 'description', 'latitude', 'longitude', 'location', 'model', 'brand', 'specifications', 'installed_date']
