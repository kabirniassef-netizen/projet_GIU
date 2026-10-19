import json
import logging
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.db.models import Q

from urban_infrastructure.notifications.models import (
    WhatsAppContact,
    WhatsAppMessage,
    WhatsAppTemplate,
)

logger = logging.getLogger(__name__)

INCIDENT_CREATED_VARIABLES = [
    'incident_id',
    'title',
    'category',
    'priority',
    'address',
]
INCIDENT_STATUS_VARIABLES = ['incident_id', 'title', 'status']


def _get_template(event):
    template = WhatsAppTemplate.objects.filter(event=event).first()
    if template:
        if not template.is_active:
            logger.warning('WhatsApp template for %s is inactive', event)
            return None
        return template, template.template_name, template.language_code

    if event == WhatsAppTemplate.Event.INCIDENT_CREATED:
        template_name = settings.WHATSAPP_TEMPLATE_NAME
        if template_name:
            return None, template_name, settings.WHATSAPP_TEMPLATE_LANGUAGE

    logger.warning('WhatsApp template for %s is not configured', event)
    return None


def _template_parameters(incident, template, event):
    values = {
        'incident_id': str(incident.pk),
        'title': incident.title,
        'category': incident.category.get_name_display(),
        'priority': incident.get_priority_display(),
        'address': ', '.join(filter(None, (
            incident.address,
            incident.commune,
            incident.department,
            incident.region,
        ))) or 'Non renseignée',
        'status': incident.get_status_display(),
    }
    defaults = (
        INCIDENT_STATUS_VARIABLES
        if event in {
            WhatsAppTemplate.Event.INCIDENT_UPDATED,
            WhatsAppTemplate.Event.INCIDENT_RESOLVED,
        }
        else INCIDENT_CREATED_VARIABLES
    )
    variables = template.variables if template and template.variables else defaults
    if not isinstance(variables, list) or any(
        variable not in values for variable in variables
    ):
        raise ValueError('La liste des variables du modèle WhatsApp est invalide.')
    return [{'type': 'text', 'text': values[variable]} for variable in variables]


def _provider_error_details(error):
    try:
        response_data = json.loads(error.read().decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return str(error.code), 'Meta a refusé la requête WhatsApp.'

    if not isinstance(response_data, dict):
        return str(error.code), 'Meta a refusé la requête WhatsApp.'
    provider_error = response_data.get('error', {})
    if not isinstance(provider_error, dict):
        return str(error.code), 'Meta a refusé la requête WhatsApp.'
    return (
        str(provider_error.get('code', error.code)),
        str(provider_error.get('message', 'Meta a refusé la requête WhatsApp.')),
    )


def _send_template_to_contacts(incident, event, contacts, restrict_recipients=False):
    if not all((
        settings.WHATSAPP_PHONE_NUMBER_ID,
        settings.WHATSAPP_ACCESS_TOKEN,
    )):
        logger.warning('WhatsApp Cloud API credentials are incomplete')
        return 0

    template_configuration = _get_template(event)
    if not template_configuration:
        return 0
    template, template_name, language_code = template_configuration

    if restrict_recipients and settings.INCIDENT_NOTIFICATION_PHONE_NUMBERS:
        contacts = contacts.filter(
            phone_number__in=settings.INCIDENT_NOTIFICATION_PHONE_NUMBERS,
        )
    contacts = contacts.select_related('user').distinct()
    if not contacts.exists():
        logger.warning(
            'No opted-in WhatsApp contacts for incident %s (%s)',
            incident.pk,
            event,
        )
        return 0

    try:
        parameters = _template_parameters(incident, template, event)
    except ValueError:
        logger.exception('Invalid WhatsApp template variables for incident %s', incident.pk)
        return 0

    endpoint = (
        f'https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/'
        f'{settings.WHATSAPP_PHONE_NUMBER_ID}/messages'
    )
    sent_count = 0
    for contact in contacts:
        payload = {
            'messaging_product': 'whatsapp',
            'to': contact.phone_number,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': language_code},
                'components': [{
                    'type': 'body',
                    'parameters': parameters,
                }],
            },
        }
        message = WhatsAppMessage.objects.create(
            contact=contact,
            template=template,
            payload=payload,
            related_model=incident._meta.label_lower,
            related_id=str(incident.pk),
        )
        api_request = urllib_request.Request(
            endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': 'Bearer ' + settings.WHATSAPP_ACCESS_TOKEN,
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib_request.urlopen(api_request, timeout=10) as response:
                response_data = json.loads(response.read().decode('utf-8'))
            provider_message_id = response_data['messages'][0]['id']
            if not isinstance(provider_message_id, str) or not provider_message_id:
                raise ValueError('Meta returned an invalid WhatsApp message ID.')
            message.mark_sent(provider_message_id)
            sent_count += 1
        except urllib_error.HTTPError as error:
            code, error_message = _provider_error_details(error)
            message.mark_failed(code=code, message=error_message)
            logger.error(
                'Meta rejected WhatsApp notification for contact %s: %s',
                contact.pk,
                error_message,
            )
        except (urllib_error.URLError, TimeoutError, OSError) as error:
            message.mark_failed(code='connection_error', message=str(error))
            logger.exception(
                'Failed to connect to Meta for WhatsApp contact %s',
                contact.pk,
            )
        except (
            KeyError,
            IndexError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
        ) as error:
            message.mark_failed(code='invalid_response', message=str(error))
            logger.exception(
                'Meta returned an invalid WhatsApp response for contact %s',
                contact.pk,
            )

    return sent_count


def notify_administrators_about_incident_via_whatsapp(incident):
    """Envoie l'alerte de création aux administrateurs consentants."""
    contacts = WhatsAppContact.objects.filter(
        is_opted_in=True,
        user__is_active=True,
    ).filter(Q(user__role='admin') | Q(user__is_staff=True))
    return _send_template_to_contacts(
        incident,
        WhatsAppTemplate.Event.INCIDENT_CREATED,
        contacts,
        restrict_recipients=True,
    )


def notify_reporter_about_incident_status_via_whatsapp(incident):
    """Envoie au citoyen consentant le modèle correspondant au nouveau statut."""
    event = (
        WhatsAppTemplate.Event.INCIDENT_RESOLVED
        if incident.status == 'resolved'
        else WhatsAppTemplate.Event.INCIDENT_UPDATED
    )
    contacts = WhatsAppContact.objects.filter(
        user=incident.reporter,
        user__is_active=True,
        is_opted_in=True,
    )
    return _send_template_to_contacts(incident, event, contacts)
