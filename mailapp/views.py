# mailapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages
import imaplib, email
from email.header import decode_header
from .models import EmailMessage  # adjust if your model is named differently

# ---------- Send view (use the robust version you already installed) ----------
def send_email_view(request):
    if request.method == 'POST':
        recipient = (request.POST.get('recipient') or '').strip()
        subject = (request.POST.get('subject') or '').strip()
        message = (request.POST.get('message') or '').strip()

        if not recipient or '@' not in recipient:
            messages.error(request, 'Please enter a valid recipient email address.')
            return render(request, 'mailapp/send_email.html', {'recipient': recipient, 'subject': subject, 'message': message})

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or getattr(settings, 'EMAIL_HOST_USER', '')
        if not from_email:
            messages.error(request, 'Server FROM address not configured.')
            return render(request, 'mailapp/send_email.html')

        try:
            sent = send_mail(subject, message, from_email, [recipient], fail_silently=False)
        except BadHeaderError:
            messages.error(request, 'Invalid header found.')
            return render(request, 'mailapp/send_email.html')
        except Exception as e:
            import traceback, sys
            traceback.print_exc(file=sys.stdout)
            messages.error(request, f'Failed to send: {e}')
            return render(request, 'mailapp/send_email.html', {'recipient': recipient, 'subject': subject, 'message': message})

        if sent:
            return redirect('mailapp:success')
        else:
            messages.error(request, 'send_mail reported 0 messages sent.')
            return render(request, 'mailapp/send_email.html')
    return render(request, 'mailapp/send_email.html')


# ---------- Success page ----------
def success_view(request):
    return render(request, 'mailapp/success.html')


# ---------- Inbox list view (reads from DB model EmailMessage) ----------
def inbox_view(request):
    # If you store fetched emails in EmailMessage model:
    try:
        emails = EmailMessage.objects.order_by('-date')[:200]
    except Exception:
        # Fallback: empty list if model missing
        emails = []
    return render(request, 'mailapp/email_list.html', {'emails': emails})


# ---------- Detail view ----------
def email_detail(request, pk):
    email_obj = get_object_or_404(EmailMessage, pk=pk)
    return render(request, 'mailapp/email_detail.html', {'email': email_obj})


# ---------- Fetch emails from IMAP and save to DB ----------
def fetch_emails(request):
    """
    Connect to IMAP, fetch recent messages and save to EmailMessage model.
    This example uses IMAP_SSL on port 993.
    """
    IMAP_HOST = getattr(settings, 'IMAP_HOST', 'imap.gmail.com')
    IMAP_PORT = getattr(settings, 'IMAP_PORT', 993)
    IMAP_USER = getattr(settings, 'IMAP_USER', '')
    IMAP_PASSWORD = getattr(settings, 'IMAP_PASSWORD', '')

    if not IMAP_USER or not IMAP_PASSWORD:
        messages.error(request, 'IMAP credentials not configured. Set IMAP_USER and IMAP_PASSWORD env vars.')
        return redirect('mailapp:email_list')

    try:
        M = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        M.login(IMAP_USER, IMAP_PASSWORD)
        M.select('INBOX')
        typ, data = M.search(None, 'ALL')
        ids = data[0].split()
        # we'll fetch last up to 50 emails
        for num in ids[-50:]:
            typ, msg_data = M.fetch(num, '(RFC822)')
            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    # decode subject
                    subj, encoding = decode_header(msg.get('Subject'))[0]
                    if isinstance(subj, bytes):
                        try:
                            subj = subj.decode(encoding or 'utf-8', errors='ignore')
                        except:
                            subj = subj.decode('utf-8', errors='ignore')
                    sender = msg.get('From')
                    date = msg.get('Date')
                    # get body
                    body = ''
                    if msg.is_multipart():
                        for p in msg.walk():
                            ctype = p.get_content_type()
                            cdisp = str(p.get('Content-Disposition'))
                            if ctype == 'text/plain' and 'attachment' not in cdisp:
                                try:
                                    body = p.get_payload(decode=True).decode('utf-8', errors='ignore')
                                except:
                                    body = p.get_payload(decode=True).decode('latin1', errors='ignore')
                                break
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            body = msg.get_payload(decode=True).decode('latin1', errors='ignore')

                    # store in DB: EmailMessage model must have at least fields: subject, sender, recipients, date, body_text
                    # Adjust according to your model
                    EmailMessage.objects.update_or_create(
                        message_id = msg.get('Message-ID'),
                        defaults = {
                            'subject': subj or '(No Subject)',
                            'sender': sender or '',
                            'recipients': IMAP_USER,
                            'date': date or '',
                            'body_text': body or '',
                        }
                    )
        M.logout()
        messages.success(request, 'Fetched emails from server (see console for details).')
    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stdout)
        messages.error(request, f'Failed to fetch emails: {e}')

    return redirect('mailapp:email_list')

