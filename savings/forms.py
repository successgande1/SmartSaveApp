from.models import Customer, Transaction, WithdrawalRequest
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
import random
import secrets
used_numbers = set()

#Customer Creation form
class CustomerCreationForm(forms.ModelForm):
    username = forms.CharField(label='Username', required=True)
    password = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    account_balance = forms.DecimalField(label='Account Balance', required=True, initial=0.0, disabled=True)
    account_number = forms.CharField(label='Account Number', required=True, disabled=True)

    class Meta:
        model = Customer
        fields = ['username', 'password', 'account_balance', 'account_number']

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
        customer.save()
        return customer
    #6 Digits account number generation function
    def generate_unique_number(self):
        used_numbers = Customer.objects.values_list('account_number', flat=True)
        while True:
            unique_number = secrets.randbelow(900000) + 100000
            if unique_number not in used_numbers:
                return str(unique_number)
            
    #Check the uniqueness of the created username and notify with message
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username