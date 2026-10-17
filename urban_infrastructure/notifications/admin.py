from django.contrib import admin

from .models import (
    Notification,
    WhatsAppContact,
    WhatsAppMessage,
    WhatsAppTemplate,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'event_type', 'is_read', 'created_at')
    list_filter = ('event_type', 'is_read')
    search_fields = ('recipient__username', 'message')


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'is_opted_in', 'opted_in_at')
    list_filter = ('is_opted_in',)
    search_fields = ('user__username', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = ('event', 'template_name', 'language_code', 'is_active')
    list_filter = ('is_active', 'language_code')


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = (
        'contact',
        'template',
        'status',
        'attempts',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('contact__phone_number', 'provider_message_id', 'related_id')
    readonly_fields = tuple(field.name for field in WhatsAppMessage._meta.fields)

    def has_add_permission(self, request):
        return False
