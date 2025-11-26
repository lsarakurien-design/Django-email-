from django.db import models

class EmailMessage(models.Model):
    uid = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=500, blank=True)
    sender = models.CharField(max_length=255, blank=True)
    recipients = models.TextField(blank=True)
    date = models.DateTimeField(null=True, blank=True)
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.subject} — {self.sender}"

class EmailAttachment(models.Model):
    message = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='attachments')
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='attachments/')
    size = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.filename

