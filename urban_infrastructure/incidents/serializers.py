from rest_framework import serializers
from .models import IncidentCategory, Incident, IncidentUpdate


class IncidentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentCategory
        fields = ['id', 'name', 'description']


class IncidentUpdateSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = IncidentUpdate
        fields = ['id', 'status', 'status_display', 'comment', 'updated_by', 'updated_by_username', 'updated_at']


class IncidentListSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='category.get_name_display', read_only=True)
    reporter_username = serializers.CharField(source='reporter.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'category', 'category_display', 'reporter_username',
            'latitude', 'longitude', 'status', 'status_display', 'priority', 'priority_display',
            'photo', 'created_at'
        ]


class IncidentDetailSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='category.get_name_display', read_only=True)
    reporter_username = serializers.CharField(source='reporter.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    updates = IncidentUpdateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'category', 'category_display', 'reporter', 'reporter_username',
            'latitude', 'longitude', 'address', 'status', 'status_display', 'priority', 'priority_display',
            'photo', 'created_at', 'updated_at', 'updates'
        ]


class IncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ['title', 'description', 'category', 'latitude', 'longitude', 'address', 'photo']
