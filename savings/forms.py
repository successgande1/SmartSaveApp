from.models import Customer, Transaction, WithdrawalRequest, ServiceCharge
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from accounts.models import Profile
import random
import secrets
from.filters import TransactionFilter, CustomerFilter
from django.core.exceptions import ValidationError
import calendar
from datetime import datetime
from calendar import month_name
from django.utils import timezone
used_numbers = set()

#Customer Creation form
class CustomerCreationForm(forms.ModelForm):
    username = forms.CharField(label='Username', required=True)
    password = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    phone = forms.CharField(label='Phone Number', required=True) #Form field form Profile Model
    address = forms.CharField(label='Address', required=True)#Form field form Profile Model
    full_name = forms.CharField(label='Full Name', required=True)#Form field form Profile Model
    account_number = forms.CharField(label='Account Number', required=True, disabled=True)
    account_balance = forms.DecimalField(label='Account Balance', required=True, initial=0.0, disabled=True)
    service_charge = forms.DecimalField(label='Service Charge', required=True, initial=200.00, disabled=True )
    
    class Meta:
        model = Customer
        fields = ['username', 'password', 'account_balance', 'service_charge', 'account_number']

    def __init__(self, added_by=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.added_by = added_by
        self.fields['account_number'].initial = self.generate_unique_number()

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        customer = Customer(customer=user, added_by=self.added_by)
        customer.account_number = self.cleaned_data['account_number']
        customer.account_balance = self.cleaned_data['account_balance']
        customer.service_charge = self.cleaned_data['service_charge']
        customer.save()

        # Create or update the associated profile
        profile, created = Profile.objects.get_or_create(user=user)
        profile.full_name = self.cleaned_data['full_name']
        profile.phone = self.cleaned_data['phone']
        profile.address = self.cleaned_data['address']
        profile.save()

        return customer

    def generate_unique_number(self):
        used_numbers = Customer.objects.values_list('account_number', flat=True)
        while True:
            unique_number = secrets.randbelow(900000) + 100000
            if unique_number not in used_numbers:
                return str(unique_number)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
    
class DepositForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_remark']

        
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if amount is None:
            raise forms.ValidationError("Amount is required.")
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        
        # Define the minimum deposit amount here
        MINIMUM_DEPOSIT_AMOUNT = 200  # Set your desired minimum amount

        if amount < MINIMUM_DEPOSIT_AMOUNT:
            raise forms.ValidationError(f"Minimum deposit amount is N{MINIMUM_DEPOSIT_AMOUNT}.")

        return amount


    
class WithdrawalRequestForm(forms.ModelForm):
    class Meta:
        model = WithdrawalRequest
        fields = ['amount']

    def __init__(self, customer, *args, **kwargs):
        self.customer = customer
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if amount is None:
            raise forms.ValidationError("Amount is required.")
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")

        if amount > self.customer.account_balance:
            raise forms.ValidationError("Withdrawal amount exceeds available balance.")

        # Check for pending withdrawal requests
        pending_requests = WithdrawalRequest.objects.filter(customer=self.customer, is_approved=False).exists()

        if pending_requests:
            raise forms.ValidationError("Customer has a pending withdrawal request.")

        # Check if the customer has been charged for the current month
        from datetime import datetime
        current_month = datetime.now().month
        charged_this_month = ServiceCharge.objects.filter(charged_customer=self.customer, charged_date__month=current_month).exists()

        if charged_this_month:
            # If the customer has already been charged this month, allow full withdrawal
            return amount

        # Calculate the minimum amount that leaves a balance equal to the service charge
        min_withdrawal_amount = self.customer.account_balance - self.customer.service_charge

        if amount > min_withdrawal_amount:
            raise forms.ValidationError("Withdrawal amount does not leave the required balance.")

        return amount

class SearchForm(forms.Form):
    search_query = forms.CharField(max_length=100, required=False, label='Search by Name, Phone or acct. No.')


class SearchTransactionForm(forms.Form): #Normal Transaction Search Form
    search_query = forms.CharField(max_length=100, required=False, label='Search by Transaction ID.')

class ReportForm(forms.Form): #Deposit, Withdrawal and Service Charge Search Form
    TRANSACTION_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('service_charge', 'Service Charge'),
    ]

    transaction_type = forms.ChoiceField(choices=TRANSACTION_CHOICES, required=True)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date())
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date())

class UserTransactionReportForm(forms.Form): #Admin User Date Range Transaction Form for All Users
    TRANSACTION_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('service_charge', 'Service Charge'),
    ]

    users = User.objects.filter(
        profile__role__in=['admin', 'cashier', 'manager'],
        profile__is_active=True
    )  # Get users with the specified profile role and active status
    user_choices = [(user.id, user.username) for user in users]

    user = forms.ChoiceField(choices=user_choices, required=True)
    transaction_type = forms.ChoiceField(choices=TRANSACTION_CHOICES, required=True)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date())
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date())


class DateRangeForm(forms.Form):  #Admin User Date Range Report Form
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date())
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date())

class StaffTransactionDateRangeForm(forms.Form): #Staff User Deposit Date Range Transaction Report Form
    TRANSACTION_CHOICES = [
        ('deposit', 'Deposit'),
        
    ]

    transaction_type = forms.ChoiceField(choices=TRANSACTION_CHOICES, required=True)
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date())
    
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date'}), initial=timezone.now().date())
    
