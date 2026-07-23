import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

RESEND_API_URL = 'https://api.resend.com/emails'


class ResendAPIBackend(BaseEmailBackend):
    """Sends mail via Resend's HTTPS API instead of SMTP.

    Render's outbound networking stalls SMTP connections (port 587 to
    smtp.resend.com hung indefinitely and got the gunicorn worker SIGKILLed
    mid-request), so plain Django SMTP backends aren't usable there. The API
    only needs outbound HTTPS, which isn't affected.
    """

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, 'RESEND_API_KEY', '')
        sent = 0
        for message in email_messages:
            payload = {
                'from': message.from_email,
                'to': message.to,
                'subject': message.subject,
                'text': message.body,
            }
            request = urllib.request.Request(
                RESEND_API_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    # Cloudflare (in front of api.resend.com) rejects requests
                    # with urllib's default User-Agent as a bot-check failure
                    # (HTTP 403, Cloudflare error 1010).
                    'User-Agent': 'ScopeCreep/1.0 (+https://scopecreep.onrender.com)',
                },
                method='POST',
            )
            try:
                with urllib.request.urlopen(request, timeout=10):
                    sent += 1
            except urllib.error.URLError:
                if not self.fail_silently:
                    raise

        return sent
