# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
from savings.models import Customer

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        role = instance.userprofile.role if hasattr(instance, 'userprofile') else None
        if role == 'admin' or role == 'cashier':
            UserProfile.objects.create(user=instance, role=role)

@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'userprofile'):
        Customer.objects.create(user=instance, account_balance=0.0)
