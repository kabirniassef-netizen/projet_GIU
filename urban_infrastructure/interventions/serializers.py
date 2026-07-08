from rest_framework import serializers
from .models import Intervention, InterventionUpdate


class InterventionUpdateSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = InterventionUpdate
        fields = ['id', 'status', 'status_display', 'comment', 'photo', 'updated_by', 'updated_by_username', 'updated_at']


class InterventionListSerializer(serializers.ModelSerializer):
    incident_title = serializers.CharField(source='incident.title', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Intervention
        fields = [
            'id', 'incident', 'incident_title', 'assigned_to', 'assigned_to_username',
            'scheduled_date', 'status', 'status_display', 'priority', 'priority_display',
            'created_at', 'completed_date'
        ]


class InterventionDetailSerializer(serializers.ModelSerializer):
    incident_title = serializers.CharField(source='incident.title', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    updates = InterventionUpdateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Intervention
        fields = [
            'id', 'incident', 'incident_title', 'assigned_to', 'assigned_to_username',
            'scheduled_date', 'estimated_duration', 'status', 'status_display', 'priority',
            'priority_display', 'notes', 'created_at', 'completed_date', 'updates'
        ]


class InterventionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intervention
        fields = ['incident', 'assigned_to', 'scheduled_date', 'estimated_duration', 'priority', 'notes']
