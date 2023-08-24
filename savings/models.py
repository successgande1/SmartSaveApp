from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime
from random import randint
import uuid
from uuid import UUID
from json import JSONEncoder


# Create your models here.
class Customer(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=6, unique=True)
    account_balance = models.DecimalField(max_digits=10, decimal_places=2)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_customer')
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    created_date = models.DateTimeField(auto_now_add=True, null=True) 
    last_updated = models.DateTimeField(auto_now_add=False, null=True) 

    def __str__(self):
        return f' {self.customer} - Account No: {self.account_number}'

class Transaction(models.Model): 
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=16, blank=True)  # 'deposit', 'withdraw'
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_transactions', related_query_name='added_transaction')
    transaction_ref = models.UUIDField(primary_key = True, editable = False, default=uuid.uuid4)
    transaction_remark = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True, null=True) 

    #Save Reference Number
    def save(self, *args, **kwargs):
         self.transaction_ref == str(uuid.uuid4())
         super().save(*args, **kwargs) 

    def __unicode__(self):
        return self.customer

    def __str__(self):
        return f' {self.customer} - Transaction Type: {self.transaction_type}'
    
    def save(self, *args, **kwargs):
        if not self.transaction_ref:
            self.transaction_ref = str(uuid.uuid4())
        super().save(*args, **kwargs)
        self.customer.account_balance += self.amount
        self.customer.last_updated = self.transaction_date
        self.customer.save()
    
class WithdrawalRequest(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_withdrawal_requests', related_query_name='added_withdrawal_request')
    request_ref = models.UUIDField(primary_key = True, editable = False, default=uuid.uuid4)
    is_approved = models.BooleanField(default=False)

    #Save Reference Number
    def save(self, *args, **kwargs):
         self.request_ref == str(uuid.uuid4())
         super().save(*args, **kwargs) 

    def __unicode__(self):
        return self.customer
    

    def __str__(self):
        return f' {self.customer} - Request Status: {self.is_approved}'
    
class ServiceCharge(models.Model):
    charged_customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    charged_amount = models.DecimalField(max_digits=10, decimal_places=2)
    charged_date = models.DateField(auto_now_add=True, null=True)

    def __str__(self):
        return f'{self.charged_customer} - N{self.charged_amount} - Date: {self.charged_date}'