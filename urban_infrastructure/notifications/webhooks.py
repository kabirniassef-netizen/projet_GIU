import hashlib
import hmac
import json
import logging
import unicodedata
from datetime import datetime, timezone as datetime_timezone

from django.conf import settings
from django.db import transaction
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    HttpResponseServerError,
)
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import WhatsAppContact, WhatsAppMessage

logger = logging.getLogger(__name__)

STATUS_RANK = {
    WhatsAppMessage.Status.PENDING: 0,
    WhatsAppMessage.Status.SENT: 1,
    WhatsAppMessage.Status.DELIVERED: 2,
    WhatsAppMessage.Status.READ: 3,
}
OPT_OUT_KEYWORDS = {
    'stop',
    'stop all',
    'stopall',
    'unsubscribe',
    'cancel',
    'end',
    'quit',
    'arret',
}


def _event_time(value):
    if value is None:
        return timezone.now()
    try:
        return datetime.fromtimestamp(float(value), tz=datetime_timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError) as error:
        raise ValueError('Horodatage WhatsApp invalide.') from error


def _apply_status(status_data):
    provider_message_id = status_data.get('id')
    provider_status = status_data.get('status')
    if not isinstance(provider_message_id, str) or not provider_message_id:
        raise ValueError('Identifiant de message WhatsApp absent.')

    status_map = {
        'sent': WhatsAppMessage.Status.SENT,
        'delivered': WhatsAppMessage.Status.DELIVERED,
        'read': WhatsAppMessage.Status.READ,
        'failed': WhatsAppMessage.Status.FAILED,
    }
    new_status = status_map.get(provider_status)
    if not new_status:
        return

    message = WhatsAppMessage.objects.filter(
        provider_message_id=provider_message_id,
    ).first()
    if not message:
        logger.warning('WhatsApp status received for unknown message ID %s', provider_message_id)
        return

    event_time = _event_time(status_data.get('timestamp'))
    if message.status == WhatsAppMessage.Status.FAILED:
        return
    if (
        new_status != WhatsAppMessage.Status.FAILED
        and STATUS_RANK.get(new_status, 0) < STATUS_RANK.get(message.status, 0)
    ):
        return

    message.status = new_status
    update_fields = ['status']
    timestamp_field = {
        WhatsAppMessage.Status.SENT: 'sent_at',
        WhatsAppMessage.Status.DELIVERED: 'delivered_at',
        WhatsAppMessage.Status.READ: 'read_at',
    }.get(new_status)
    if timestamp_field:
        setattr(message, timestamp_field, event_time)
        update_fields.append(timestamp_field)
    if new_status == WhatsAppMessage.Status.FAILED:
        errors = status_data.get('errors') or []
        error = errors[0] if errors and isinstance(errors[0], dict) else {}
        error_data = error.get('error_data', {})
        if not isinstance(error_data, dict):
            error_data = {}
        message.error_code = str(error.get('code', ''))
        message.error_message = str(
            error_data.get('details')
            or error.get('message')
            or '',
        )
        update_fields.extend(['error_code', 'error_message'])
    message.save(update_fields=update_fields)


def _apply_inbound_message(message_data):
    sender = message_data.get('from')
    if not isinstance(sender, str) or not sender:
        raise ValueError('Numéro expéditeur WhatsApp absent.')
    phone_number = '+' + sender.lstrip('+')
    contact = WhatsAppContact.objects.filter(phone_number=phone_number).first()
    if not contact:
        logger.info('Incoming WhatsApp message from an unregistered contact')
        return

    event_time = _event_time(message_data.get('timestamp'))
    if not contact.last_inbound_at or event_time > contact.last_inbound_at:
        contact.last_inbound_at = event_time
        contact.save(update_fields=['last_inbound_at', 'updated_at'])

    text = message_data.get('text', {})
    body = text.get('body', '') if isinstance(text, dict) else ''
    if not isinstance(body, str):
        body = ''
    normalized_body = unicodedata.normalize('NFKD', body.casefold())
    keyword = ''.join(
        character for character in normalized_body
        if not unicodedata.combining(character)
    ).strip(' \t\n\r!.,;:')
    if keyword in OPT_OUT_KEYWORDS and contact.is_opted_in:
        contact.is_opted_in = False
        contact.opted_out_at = event_time
        contact.save(update_fields=[
            'is_opted_in',
            'opted_out_at',
            'updated_at',
        ])


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        verify_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
        if not verify_token:
            return HttpResponseServerError('Webhook WhatsApp non configuré.')
        if (
            request.GET.get('hub.mode') != 'subscribe'
            or not hmac.compare_digest(
                request.GET.get('hub.verify_token', ''),
                verify_token,
            )
        ):
            return HttpResponseForbidden('Jeton de vérification invalide.')
        challenge = request.GET.get('hub.challenge', '')
        return HttpResponse(challenge, content_type='text/plain')

    if request.method != 'POST':
        return HttpResponseNotAllowed(['GET', 'POST'])

    app_secret = settings.WHATSAPP_APP_SECRET
    if not app_secret:
        return HttpResponseServerError('Signature du webhook WhatsApp non configurée.')
    supplied_signature = request.headers.get('X-Hub-Signature-256', '')
    expected_signature = 'sha256=' + hmac.new(
        app_secret.encode('utf-8'),
        request.body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(supplied_signature, expected_signature):
        return HttpResponseForbidden('Signature WhatsApp invalide.')

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponseBadRequest('JSON WhatsApp invalide.')
    if not isinstance(payload, dict) or not isinstance(payload.get('entry', []), list):
        return HttpResponseBadRequest('Structure du webhook WhatsApp invalide.')

    try:
        with transaction.atomic():
            for entry in payload.get('entry', []):
                if not isinstance(entry, dict):
                    raise ValueError('Entrée de webhook WhatsApp invalide.')
                for change in entry.get('changes', []):
                    if not isinstance(change, dict):
                        raise ValueError('Modification de webhook WhatsApp invalide.')
                    value = change.get('value', {})
                    if not isinstance(value, dict):
                        raise ValueError('Valeur de webhook WhatsApp invalide.')
                    for status_data in value.get('statuses', []):
                        if not isinstance(status_data, dict):
                            raise ValueError('Statut WhatsApp invalide.')
                        _apply_status(status_data)
                    for message_data in value.get('messages', []):
                        if not isinstance(message_data, dict):
                            raise ValueError('Message entrant WhatsApp invalide.')
                        _apply_inbound_message(message_data)
    except (TypeError, ValueError):
        logger.exception('Invalid WhatsApp webhook payload')
        return HttpResponseBadRequest('Données du webhook WhatsApp invalides.')

    return HttpResponse('EVENT_RECEIVED', content_type='text/plain')
