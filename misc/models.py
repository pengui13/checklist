from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class ActivityLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'create', 'Created'
        UPDATE = 'update', 'Updated'
        DELETE  = 'delete', 'Deleted'
        LOGIN = 'login', 'Logged In'
        LOGOUT = 'logout', 'logged out'
        INVITE = 'invite', 'Invited'
        JOIN = 'join', 'Joined'
        EXPORT = 'export', 'Exported'
        UPLOAD = 'upload', 'Uploaded'

    user = models.ForeignKey(
        'users.User',
        on_delete = models.SET_NULL,
        null = True, 
        blank = True,
        related_name = 'activity_logs'
    )
    firm = models.ForeignKey(
        'organisation.Firm',
        on_delete=models.CASCADE,
        null = True,
        blank = True,
        related_name = 'activity_logs'
    )
    action = models.CharField(max_length=20, choices = Action.choices)
    description = models.TextField(blank = True)
    content_type = models.ForeignKey(
        ContentType, on_delete = models.SET_NULL,
        null = True, blank = True
    )
    object_id = models.PositiveIntegerField(null = True, blank = True)
    content_object = GenericForeignKey('content_type', 'object_id')
    changes = models.JSONField(default = dict, blank = True)
    ip_address = models.GenericIPAddressField(null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields = ['firm', '-created_at'],),
            models.Index(fields = ['user', '-created_at'],),
            models.Index(fields = ['content_type', 'object_id'],),
            
        ]
    def __str__(self):
        return f'{self.user} | {self.action} | {self.created_at}'
    
    @classmethod
    def log(cls, action, user = None, firm = None, obj = None, description = '', changes = None, ip_address = None):
        log_entry = cls(
            action = action,
            user = user,
            firm = firm or getattr(user, 'firm', None),
            description = description,
            changes = changes or {},
            ip_address = ip_address
        )
        if obj:
            log_entry.content_type = ContentType.objects.get_for_model(obj)
            log_entry.object_id = obj.pk
            
        log_entry.save()
        return log_entry