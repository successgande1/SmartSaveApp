from django.contrib import admin
from .models import *
# Register your models here.


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'role', 'address', 'image', 'last_updated')
    list_per_page = 6
admin.site.register(Profile, ProfileAdmin)