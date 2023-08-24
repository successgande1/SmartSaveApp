from.models import Customer, Transaction, WithdrawalRequest
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from accounts.models import Profile
import random
import secrets
from.filters import TransactionFilter, CustomerFilter
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

class SearchTransactionForm(forms.Form):
    transaction_ref = forms.CharField(max_length=100, required=False)
   

    def search(self):
        queryset = Transaction.objects.all()
        filter_params = {}

        transaction_ref = self.cleaned_data.get('transaction_ref')
        if transaction_ref:
            filter_params['transaction_ref'] = transaction_ref
        return queryset.filter(**filter_params)