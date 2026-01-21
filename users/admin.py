from django.contrib import admin
from users.models import User, Invitation
admin.site.register(User)
admin.site.register(Invitation)
