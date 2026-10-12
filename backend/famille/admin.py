from django.contrib import admin

from .models import ChildDevice, EnrollInvite, InstalledApp, ParentProfile, Position

admin.site.register([ParentProfile, EnrollInvite, ChildDevice, Position, InstalledApp])
