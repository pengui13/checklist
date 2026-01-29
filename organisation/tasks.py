from celery import shared_task
from django.conf import settings 
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from datetime import timedelta
from organisation.models import Task
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
    
@shared_task
def check_all_task_statuses():

    now = timezone.now()

    Task.objects.filter(
        end_datetime__isnull=False,
        end_datetime__lt=now,
    ).exclude(
        status__in=['completed', 'cancelled', 'expired']
    ).update(status='expired')

    soon = now + timedelta(hours=1)
    expiring_soon = Task.objects.filter(
        end_datetime__gt=now,
        end_datetime__lte=soon,
        status__in=['new', 'planned', 'active'],
    )

    for task in expiring_soon:
        pass
