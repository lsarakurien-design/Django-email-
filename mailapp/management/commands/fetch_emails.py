import imaplib
import email
from django.core.management.base import BaseCommand
from django.conf import settings
from mailapp.models import EmailMessage, EmailAttachment
from django.core.files.base import ContentFile
import re

class Command(BaseCommand):
    help = 'Fetch emails via IMAP and save to DB'

    def handle(self, *args, **kwargs):
        M = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        M.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        M.select(settings.IMAP_FOLDER)

        result, data = M.search(None, 'ALL')
        if result != 'OK':
            self.stdout.write("No messages found!")
            return

        for num in data[0].split():
            result, msg_data = M.fetch(num, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            uid = msg.get('Message-ID', num.decode())
            if EmailMessage.objects.filter(uid=uid).exists():
                continue

            subject = msg.get('Subject', '')
            sender = msg.get('From', '')
            to = msg.get('To', '')
            date = email.utils.parsedate_to_datetime(msg.get('Date'))

            body_text = ''
            body_html = ''
            attachments = []

            for part in msg.walk():
                content_disposition = str(part.get('Content-Disposition'))
                content_type = part.get_content_type()
                payload = part.get_payload(decode=True)

                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append((filename, payload))
                elif content_type == 'text/plain':
                    body_text += payload.decode(errors='ignore')
                elif content_type == 'text/html':
                    body_html += payload.decode(errors='ignore')

            em = EmailMessage.objects.create(
                uid=uid, subject=subject, sender=sender, recipients=to,
                date=date, body_text=body_text, body_html=body_html
            )

            for filename, content in attachments:
                safe_name = re.sub(r'[^A-Za-z0-9.\-_]+', '_', filename)
                attach = EmailAttachment(message=em, filename=safe_name)
                attach.file.save(safe_name, ContentFile(content))
                attach.save()

        M.close()
        M.logout()
        self.stdout.write(self.style.SUCCESS('Emails fetched successfully!'))
