from rest_framework import serializers
from .models import IncidentCategory, Incident, IncidentUpdate


class IncidentCategorySerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = IncidentCategory
        fields = ['id', 'name', 'name_display', 'description']


class IncidentUpdateSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    updated_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = IncidentUpdate
        fields = [
            'id', 'status', 'status_display', 'comment', 'updated_by',
            'updated_by_username', 'updated_by_name', 'updated_at',
        ]

    def get_updated_by_name(self, update):
        if not update.updated_by:
            return None
        return update.updated_by.get_full_name() or update.updated_by.username


def _latest_intervention(incident):
    # Utilise le prefetch lorsqu'il est disponible pour éviter les requêtes N+1.
    interventions = list(incident.interventions.all())
    if not interventions:
        return None
    return max(interventions, key=lambda item: (item.created_at, item.pk))


class IncidentListSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='category.get_name_display', read_only=True)
    category_code = serializers.CharField(source='category.name', read_only=True)
    reporter_username = serializers.CharField(source='reporter.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    allowed_next_statuses = serializers.SerializerMethodField()
    intervention = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'tracking_code', 'title', 'description', 'category', 'category_display',
            'category_code', 'reporter_username',
            'region', 'department', 'commune', 'address', 'status', 'status_display',
            'priority', 'priority_display', 'allowed_next_statuses', 'intervention',
            'photo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'tracking_code']

    def get_allowed_next_statuses(self, incident):
        return incident.allowed_next_statuses()

    def get_intervention(self, incident):
        intervention = _latest_intervention(incident)
        if not intervention:
            return None
        return {
            'id': intervention.pk,
            'status': intervention.status,
            'status_display': intervention.get_status_display(),
            'assigned_to': intervention.assigned_to_id,
            'assigned_to_name': (
                intervention.assigned_to.get_full_name() or intervention.assigned_to.username
            ) if intervention.assigned_to else None,
            'scheduled_date': intervention.scheduled_date,
        }


class IncidentDetailSerializer(IncidentListSerializer):
    updates = IncidentUpdateSerializer(many=True, read_only=True)

    class Meta(IncidentListSerializer.Meta):
        fields = IncidentListSerializer.Meta.fields + ['reporter', 'updates']


class IncidentManageSerializer(serializers.ModelSerializer):
    """Modification d'un signalement par un gestionnaire (le statut suit son workflow)."""

    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'category', 'priority',
            'region', 'department', 'commune', 'address',
        ]
        read_only_fields = ['id']


class IncidentCreateSerializer(serializers.ModelSerializer):
    MAX_PHOTO_SIZE = 5 * 1024 * 1024
    region = serializers.CharField(max_length=100)
    department = serializers.CharField(max_length=100)
    commune = serializers.CharField(max_length=100)
    address = serializers.CharField(max_length=300, required=False, allow_blank=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'tracking_code', 'title', 'description', 'category',
            'region', 'department', 'commune', 'address', 'photo',
        ]
        read_only_fields = ['id', 'tracking_code']

    def validate_photo(self, photo):
        if photo and photo.size > self.MAX_PHOTO_SIZE:
            raise serializers.ValidationError('La photo ne doit pas dépasser 5 Mio.')
        return photo


class PublicIncidentCreateSerializer(IncidentCreateSerializer):
    class Meta(IncidentCreateSerializer.Meta):
        fields = IncidentCreateSerializer.Meta.fields


class PublicIncidentTrackingSerializer(serializers.ModelSerializer):
    """Vue publique minimale : aucune donnée personnelle n'est exposée."""
    category_display = serializers.CharField(source='category.get_name_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    timeline = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'tracking_code', 'title', 'category_display', 'commune', 'status',
            'status_display', 'created_at', 'updated_at', 'timeline',
        ]

    def get_timeline(self, incident):
        return [
            {
                'status': update.status,
                'status_display': update.get_status_display(),
                'date': update.updated_at,
            }
            for update in sorted(incident.updates.all(), key=lambda item: item.updated_at)
        ]
