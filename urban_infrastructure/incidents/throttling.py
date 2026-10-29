import secrets

from django.conf import settings
from rest_framework.throttling import AnonRateThrottle


def is_chatbot_request(request):
    """Le chatbot (Typebot, n8n…) s'identifie avec la clé partagée CHATBOT_API_KEY."""
    expected = settings.CHATBOT_API_KEY
    provided = request.headers.get('X-Chatbot-Key', '')
    return bool(expected) and secrets.compare_digest(provided, expected)


class PublicIncidentRateThrottle(AnonRateThrottle):
    """Limite anonyme par IP, sauf pour le chatbot.

    Toutes les requêtes du chatbot partent du même serveur : sans quota dédié,
    l'ensemble des citoyens qui l'utilisent se partageraient 20 requêtes par heure.
    """

    def allow_request(self, request, view):
        if is_chatbot_request(request):
            self.scope = 'chatbot'
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)
