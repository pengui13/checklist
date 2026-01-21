from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings 
from django.core.mail import EmailMultiAlternatives

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, message, recipient_list, from_email=None, html_message=None):
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=list(recipient_list),
        )
        if html_message:
            email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as exc:
        raise self.retry(exc=exc)