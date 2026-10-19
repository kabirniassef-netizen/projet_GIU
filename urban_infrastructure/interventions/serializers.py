from rest_framework import serializers
from urban_infrastructure.incidents.models import Incident
from .models import Intervention, InterventionUpdate


class InterventionUpdateSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = InterventionUpdate
        fields = ['id', 'status', 'status_display', 'comment', 'photo', 'updated_by', 'updated_by_username', 'updated_at']


class InterventionListSerializer(serializers.ModelSerializer):
    incident_title = serializers.CharField(source='incident.title', read_only=True)
    incident_location = serializers.SerializerMethodField()
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    allowed_next_statuses = serializers.SerializerMethodField()
    
    class Meta:
        model = Intervention
        fields = [
            'id', 'incident', 'incident_title', 'incident_location', 'assigned_to',
            'assigned_to_username', 'assigned_to_name', 'scheduled_date',
            'estimated_duration', 'status', 'status_display', 'priority',
            'priority_display', 'allowed_next_statuses', 'notes', 'created_at',
            'completed_date',
        ]

    def get_incident_location(self, intervention):
        incident = intervention.incident
        return ', '.join(filter(None, (incident.address, incident.commune))) or None

    def get_assigned_to_name(self, intervention):
        if not intervention.assigned_to:
            return None
        return intervention.assigned_to.get_full_name() or intervention.assigned_to.username

    def get_allowed_next_statuses(self, intervention):
        return sorted(intervention.ALLOWED_STATUS_TRANSITIONS.get(intervention.status, set()))


class InterventionDetailSerializer(InterventionListSerializer):
    updates = InterventionUpdateSerializer(many=True, read_only=True)
    
    class Meta(InterventionListSerializer.Meta):
        fields = InterventionListSerializer.Meta.fields + ['updates']


class InterventionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intervention
        fields = ['id', 'incident', 'assigned_to', 'scheduled_date', 'estimated_duration', 'priority', 'notes', 'status']
        read_only_fields = ['id', 'status']

    def validate_estimated_duration(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('La durée estimée doit être positive.')
        return value

    def validate_incident(self, incident):
        if incident.status != Incident.VALIDATED:
            raise serializers.ValidationError(
                'Un incident doit être validé avant la planification d’une intervention.'
            )
        return incident

    def validate_assigned_to(self, user):
        if user and user.role != 'agent':
            raise serializers.ValidationError('L’intervention doit être attribuée à un agent technique.')
        return user


class InterventionManageSerializer(serializers.ModelSerializer):
    """Replanification ou réaffectation d'une intervention existante."""

    class Meta:
        model = Intervention
        fields = ['id', 'assigned_to', 'scheduled_date', 'estimated_duration', 'priority', 'notes']
        read_only_fields = ['id']

    def validate_assigned_to(self, user):
        if user and user.role != 'agent':
            raise serializers.ValidationError('L’intervention doit être attribuée à un agent technique.')
        return user

    def validate(self, attrs):
        if self.instance and self.instance.status in {
            Intervention.COMPLETED, Intervention.CANCELLED,
        }:
            raise serializers.ValidationError(
                'Une intervention terminée ou annulée ne peut plus être modifiée.'
            )
        return attrs
