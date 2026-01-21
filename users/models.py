from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from datetime import timedelta
from django.conf import settings


class User(AbstractUser):
    hex_color = models.CharField(max_length=6, null=True, blank=True)
    is_admin = models.BooleanField(default = False)
    is_creator = models.BooleanField(default = False)
    firm = models.ForeignKey(
        'organisation.Firm', 
        on_delete=models.SET_NULL,
        related_name='users',
        null=True,
        blank=True
    )
    
    def needs_onboarding(self):
        return self.firm is None or not self.hex_color
    
    class Meta:
        db_table = 'users'
    
from django.utils import timezone 

class Invitation(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    project = models.ForeignKey("organisation.Project", on_delete=models.CASCADE, related_name="invitations")
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_invitations")

    token = models.CharField(max_length=100, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")

    expires_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    accepted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="accepted_invitations"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at
