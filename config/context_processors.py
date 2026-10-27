from django.conf import settings


def chatbot(request):
    """Expose la configuration de la bulle Typebot (instance auto-hébergée) aux templates."""
    if not (settings.TYPEBOT_ID and settings.TYPEBOT_API_HOST):
        return {}
    return {
        'typebot_config': {
            'typebot': settings.TYPEBOT_ID,
            'apiHost': settings.TYPEBOT_API_HOST,
        },
    }
