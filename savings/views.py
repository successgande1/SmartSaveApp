from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,  get_object_or_404
from.models import Customer, Transaction, WithdrawalRequest
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count, Sum
import datetime
from.forms import *

# Create your views here.
@login_required(login_url='accounts-login')
def create_customer(request):
    #Get Customers
    customers = Customer.objects.order_by('-created_date')[:5]
    if request.method == 'POST':
        form = CustomerCreationForm(added_by=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            account_number = form.cleaned_data['account_number']
            account_balance = form.cleaned_data['account_balance']
            messages.success(request, f'Deposit Acct. No: {account_number} for {username} with {password} Password and N{account_balance} Bal. Created Successfully.')
            return redirect('savings-account')
    else:
        form = CustomerCreationForm()
    
    context = {
        'customers':customers,
        'page_title':'Create Account',
        'form': form
        }
    return render(request, 'savings/create_customer_account.html', context)