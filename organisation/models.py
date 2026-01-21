from django.db import models
from datetime import datetime
from django.conf import settings
import os
from django.utils import timezone

class Firm(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        db_table = 'firm'
        
    @property
    def creator(self):
        return self.users.filter(is_creator = True).first()
    
    def set_creator(self, user):
        self.users.update(is_creator = False)
        user.firm = self
        user.is_creator = True
        user.is_admin = True    
        user.save()
        
def get_first_month_day():
    today = datetime.now()
    return datetime(today.year, today.month, 1)

class Project(models.Model):
    RECURRENCE_CHOICES  = [
        ('weekly','Wöchentlich'),
        ('monthly','Monatlich'),
        ('quarterly','Vierteljährlich'),
        ('yearly','Jährlich')
        
    ]
    STATUS_CHOICES = [
        ('draft','Entwurf'),
        ('finished','Abgeschlossen'),
        ('planned','In Planung'),
        ('cancelled','Storniert'),
        ('active','In Arbeit')
    ]
    name = models.CharField(max_length=100)
    firm = models.ForeignKey(Firm, on_delete = models.CASCADE, related_name='projects')
    partner = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name='partners')
    start_date = models.DateField(default = get_first_month_day)
    is_one_time = models.BooleanField(default = True)
    recurrence_pattern = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, 
                                           blank = True, null = True)
    end_date = models.DateField(blank=True,null = True)
    partner = models.ForeignKey(
    Firm,
    on_delete=models.CASCADE,
    related_name="partners",
    null=True,
    blank=True,
    )

    status = models.CharField(choices = STATUS_CHOICES, default = 'planned')
    class Meta:
        db_table = 'project'
    
    def __str__(self):
        return f'{self.name}'
        

class Task(models.Model):
    TASK_CHOICES = [
        ('cancelled', 'Storniert'),
        ('active', 'Aktiv'),
        ('new', 'Neu'),
        ('completed', 'Fertig'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_datetime = models.DateTimeField(null = True, blank = True)
    end_datetime = models.DateTimeField(null = True, blank = True)
    duration = models.IntegerField(default = 2) # in hours
    assigned_users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name = 'tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    level = models.PositiveSmallIntegerField(default = 1)
    is_veto = models.BooleanField(default = False)
    status = models.CharField(max_length = 50, choices = TASK_CHOICES, default = 'new')
    class Meta:
        db_table = 'task'

def task_attachment_path(instance, filename):
    return f'task_attachments/task_{instance.task.id}/{filename}'

class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete = models.CASCADE, related_name = 'attachments')
    file = models.FileField(upload_to = task_attachment_path, max_length=500)
    filename = models.CharField(max_length = 200, blank = True)
    file_size = models.IntegerField(blank = True, null = True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete= models.SET_NULL,
        null = True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_attachment'
        ordering = ['-uploaded_at']
        
    def save(self, *args, **kwargs):
        if self.file:
            self.filename = os.path.basename(self.file.name)
            self.file_size = self.file.size
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.filename} | {self.task.name}"
      
    @property
    def file_type(self):
        return os.path.splitext(self.filename)[1].lower()
    
    @property
    def is_image(self):
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        return self.file_type in image_extensions
    
