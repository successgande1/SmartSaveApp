from django.contrib import admin
from .models import *
# Register your models here.


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('staff', 'full_name', 'phone', 'role', 'address', 'image', 'last_updated')
    list_per_page = 6
admin.site.register(UserProfile, UserProfileAdmin)