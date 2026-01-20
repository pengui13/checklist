from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    hex_color = models.CharField(max_length=6, null = True, blank = True)
    
    class Meta:
        db_table = 'users'
        