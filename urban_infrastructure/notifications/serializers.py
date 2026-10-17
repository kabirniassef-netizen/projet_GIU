from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    related_object_type = serializers.SerializerMethodField()
    related_object_id = serializers.IntegerField(source='object_id', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'event_type', 'message', 'related_object_type',
            'related_object_id', 'is_read', 'created_at',
        ]
        read_only_fields = [
            'id', 'event_type', 'message', 'related_object_type',
            'related_object_id', 'created_at',
        ]

    def get_related_object_type(self, notification):
        if notification.content_type_id:
            return notification.content_type.model
        return None