from rest_framework import serializers
from .models import IncidentCategory, Incident, IncidentUpdate


class IncidentCategorySerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = IncidentCategory
        fields = ['id', 'name', 'name_display', 'description']


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
            'region', 'department', 'commune', 'status', 'status_display',
            'priority', 'priority_display',
            'photo', 'created_at'
        ]
        read_only_fields = ['status']


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
            'region', 'department', 'commune', 'status', 'status_display',
            'priority', 'priority_display',
            'photo', 'created_at', 'updated_at', 'updates'
        ]
        read_only_fields = ['status']


class IncidentCreateSerializer(serializers.ModelSerializer):
    MAX_PHOTO_SIZE = 5 * 1024 * 1024
    region = serializers.CharField(max_length=100)
    department = serializers.CharField(max_length=100)
    commune = serializers.CharField(max_length=100)

    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'category',
            'region', 'department', 'commune', 'photo',
        ]
        read_only_fields = ['id']

    def validate_photo(self, photo):
        if photo and photo.size > self.MAX_PHOTO_SIZE:
            raise serializers.ValidationError('La photo ne doit pas dépasser 5 Mio.')
        return photo
