from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime
from random import randint
import uuid
from uuid import UUID
from json import JSONEncoder
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum


# Create your models here.
class Customer(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=6, unique=True)
    account_balance = models.DecimalField(max_digits=10, decimal_places=2)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_customer')
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    created_date = models.DateTimeField(auto_now_add=True, null=True) 
    last_updated = models.DateTimeField(auto_now_add=False, null=True) 

    def update_account_balance(self, amount):
        self.account_balance -= amount
        self.last_updated = timezone.now()
        self.save()

    def set_pending_withdrawal_status(self):
        return self.withdrawalrequest_set.filter(is_approved=False).exists()
    
    #Method for Total account balances of customers belonging to logged in user for the Month
    @classmethod
    def get_user_total_customer_balance(cls, year, month, user):
        return cls.objects.filter(
            added_by=user,
            created_date__year=year,
            created_date__month=month
        ).aggregate(total_balance=Sum('account_balance'))['total_balance'] or 0.00
    
    #Method for Total account balances of all customers in the Month
    @classmethod
    def get_total_customers_balance(cls, year, month):
        return cls.objects.filter(
            last_updated__year=year,
            last_updated__month=month
        ).aggregate(total_balance=Sum('account_balance'))['total_balance'] or 0.00

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


    @classmethod
    def get_total_deposits(cls, year, month): #Method for calculating Total Current Month Deposit
        return cls.objects.filter(
            transaction_type='deposit',
            transaction_date__year=year,
            transaction_date__month=month
        ).aggregate(total_deposits=Sum('amount'))['total_deposits'] or 0.00
    

    
    @classmethod
    def get_total_deposit_today(cls, year, month, day):# Method for calculating Total Deposit for the day
        return cls.objects.filter(
            transaction_type='deposit',
            transaction_date__year=year,
            transaction_date__month=month,
            transaction_date__day=day
        ).aggregate(total_deposits=Sum('amount'))['total_deposits'] or 0.00

    @classmethod
    def get_total_withdrawals(cls, year, month): #Method for calculating Total Current Month Withdraw
        return cls.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=year,
            transaction_date__month=month
        ).aggregate(total_withdrawals=Sum('amount'))['total_withdrawals'] or 0.00
    
    # Method for calculating Total Deposite by user for the day
    @classmethod
    def get_user_total_desposited_today(cls, year, month, day, user):  
        return cls.objects.filter(
            transaction_type='deposit',
            transaction_date__year=year,
            transaction_date__month=month,
            transaction_date__day=day,
            added_by = user
        ).aggregate(total_withdrawals=Sum('amount'))['total_withdrawals'] or 0.00
    
     # Method for calculating Total withdrawal Added by user for the day
    @classmethod
    def get_user_total_withdrawal_today(cls, year, month, day, user):  
        return cls.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=year,
            transaction_date__month=month,
            transaction_date__day=day,
            added_by = user
        ).aggregate(total_withdrawals=Sum('amount'))['total_withdrawals'] or 0.00
    
    @classmethod
    def get_total_withdrawal_today(cls, year, month, day):  # Method for calculating Total Withdrawal for the day
        return cls.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=year,
            transaction_date__month=month,
            transaction_date__day=day
        ).aggregate(total_withdrawals=Sum('amount'))['total_withdrawals'] or 0.00

    def save(self, *args, **kwargs):
        if not self.transaction_ref:
            self.transaction_ref = str(uuid.uuid4())
        super().save(*args, **kwargs)

        # Update customer's account balance and last_updated attributes
        if self.transaction_type == 'deposit':
            self.customer.account_balance += self.amount
            self.customer.last_updated = self.transaction_date
            self.customer.save()
        elif self.transaction_type == 'withdraw':
            self.customer.account_balance -= self.amount
            self.customer.last_updated = self.transaction_date
            self.customer.save()

    def __str__(self):
        return f' {self.customer} - Transaction Type: {self.transaction_type}'
    
    
class WithdrawalRequest(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_withdrawal_requests', related_query_name='added_withdrawal_request')
    request_ref = models.UUIDField(primary_key = True, editable = False, default=uuid.uuid4)
    is_approved = models.BooleanField(default=False)
    request_date = models.DateTimeField(auto_now_add=True)
    request_date_local = models.DateTimeField(auto_now_add=True)

    @classmethod #Method for getting all customer total withdrawal Request for the day
    def get_total_withdrawal_request(cls, year, month, day):
        total_request = cls.objects.filter(
            request_date__year=year,
            request_date__month=month,
            request_date__day=day
        ).aggregate(total_request=Sum('amount'))['total_request']
        return total_request or 0.00
    
    @classmethod #Method for getting total withdrawal request by logged in user
    def get_total_withdrawal_request_by_user(cls, year, month, day, user):
        total_request = cls.objects.filter(
            request_date__year=year,
            request_date__month=month,
            request_date__day=day,
            added_by=user
        ).aggregate(total_request=Sum('amount'))['total_request']
        return total_request or 0.00



    #Save Reference Number
    def save(self, *args, **kwargs):
         self.request_ref == str(uuid.uuid4())
         self.request_date_local = timezone.localtime(self.request_date)
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