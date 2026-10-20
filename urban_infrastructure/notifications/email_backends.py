import base64
import json
import logging
import re
from email.utils import parseaddr
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'
_CID_IMAGE_PATTERN = re.compile(r'<img[^>]+src="cid:[^"]*"[^>]*>')
_JPEG_EXTENSION_ALIASES = {'jfif', 'jpe', 'pjpeg', 'pjp'}
logger = logging.getLogger(__name__)


class BrevoEmailBackend(BaseEmailBackend):
    """Envoie les e-mails via l'API HTTP de Brevo.

    L'hébergement Render gratuit bloque les ports SMTP : l'API HTTPS permet
    malgré tout de livrer les notifications dans la boîte de chaque utilisateur.
    """

    def __init__(self, api_key=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = api_key or settings.BREVO_API_KEY

    def send_messages(self, email_messages):
        sent_count = 0
        for message in email_messages:
            if not message.recipients():
                continue
            try:
                self._send(message)
            except OSError:
                if not self.fail_silently:
                    raise
            else:
                sent_count += 1
        return sent_count

    def _send(self, message):
        sender_name, sender_email = parseaddr(message.from_email)
        sender = {'email': sender_email}
        if sender_name:
            sender['name'] = sender_name
        payload = {
            'sender': sender,
            'to': [{'email': address} for address in message.to],
            'subject': message.subject,
            'textContent': message.body,
        }
        if message.cc:
            payload['cc'] = [{'email': address} for address in message.cc]
        if message.bcc:
            payload['bcc'] = [{'email': address} for address in message.bcc]

        attachments = []
        for content, mime_type in getattr(message, 'alternatives', []):
            if mime_type == 'text/html':
                # Brevo ne gère pas les images « cid: » : la photo est jointe au message.
                payload['htmlContent'] = _CID_IMAGE_PATTERN.sub('', content)
        photo_content = getattr(message, 'photo_content', None)
        if photo_content:
            attachments.append({
                'name': _brevo_attachment_name(message.photo_name),
                'content': base64.b64encode(photo_content).decode('ascii'),
            })
        for attachment in message.attachments:
            if isinstance(attachment, tuple) or hasattr(attachment, 'filename'):
                filename, content = attachment[0], attachment[1]
                if isinstance(content, str):
                    content = content.encode('utf-8')
                attachments.append({
                    'name': filename,
                    'content': base64.b64encode(content).decode('ascii'),
                })
        if attachments:
            payload['attachment'] = attachments

        try:
            self._post(payload)
        except urllib_error.HTTPError as error:
            detail = error.read().decode('utf-8', errors='replace')
            if not (error.code == 400 and attachments):
                raise OSError(f'Brevo API error {error.code}: {detail}') from error
            # Une pièce jointe refusée ne doit pas empêcher la notification d'arriver.
            logger.warning('Brevo rejected attachments, sending without them: %s', detail)
            del payload['attachment']
            try:
                self._post(payload)
            except urllib_error.HTTPError as retry_error:
                retry_detail = retry_error.read().decode('utf-8', errors='replace')
                raise OSError(
                    f'Brevo API error {retry_error.code}: {retry_detail}',
                ) from retry_error

    def _post(self, payload):
        api_request = urllib_request.Request(
            BREVO_API_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'api-key': self.api_key,
            },
            method='POST',
        )
        with urllib_request.urlopen(api_request, timeout=10) as response:
            response.read()


def _brevo_attachment_name(filename):
    # Brevo refuse certaines extensions JPEG (« .jfif », « .jpe ») : on les présente en « .jpg ».
    stem, dot, extension = filename.rpartition('.')
    if dot and extension.lower() in _JPEG_EXTENSION_ALIASES:
        return f'{stem}.jpg'
    return filename
