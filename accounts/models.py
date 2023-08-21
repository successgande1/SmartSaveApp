from imagekit.processors import ResizeToFill, Transpose
from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime
from random import randint
import uuid
from uuid import UUID
from imagekit.models import ProcessedImageField
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


#File Extension Validator
@deconstructible
class FileExtensionValidator:
    """ImageKit Validation Decorator"""
    def __init__(self, extensions):
        self.extensions = extensions

    def __call__(self, value):
        extension = value.name.split('.')[-1].lower()
        if extension not in self.extensions:
            valid_extensions = ', '.join(self.extensions)
            raise ValidationError(f"Invalid file extension. Only {valid_extensions} files are allowed.")

image_extensions = ['jpeg', 'jpg', 'gif', 'png']

class UserProfile(models.Model):
    staff = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # 'admin', 'cashier', 'customer'
    full_name = models.CharField(max_length=60, blank=True)
    phone = PhoneNumberField()
    address = models.CharField(max_length=160, blank=True)
    image = ProcessedImageField(
                                    upload_to='profile_images',
                                    processors=[Transpose(), ResizeToFill(150, 200)],
                                    format='JPEG',
                                    options={'quality': 97},
                                    validators=[FileExtensionValidator(image_extensions)],
                                    default='avatar.jpg'
                                )
    last_updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.staff.username}-Profile'


