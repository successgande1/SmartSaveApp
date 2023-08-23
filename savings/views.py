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
    logged_user = request.user
    #Get Customers
    customers = Customer.objects.order_by('-created_date')[:10]
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

#Customer List View
@login_required(login_url='accounts-login')
def customer_lsit(request):
    #Get list of customers
    customers = Customer.objects.order_by('-created_date')
     # Paginate the properties
    paginator = Paginator(customers, 5)  # Show 6 properties per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title':'Customer List',
        'customers':page_obj,
    }
    return render(request, 'savings/customer_list.html', context)


#Customer Deposit View
@login_required(login_url='accounts-login')
def customer_deposit(request, pk):
    #Get the Customer by Product Key
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.customer = customer
            transaction.transaction_type = 'deposit'
            transaction.added_by = request.user
            transaction.save()
            deposited = form.cleaned_data['amount']
        messages.success(request, f'N{deposited} Deposited Successfully for Acct. No:{customer.account_number}')
        return redirect('customer_deposit', pk=pk)
    else:
        form = DepositForm()
    context = {
        'customer':customer,
        'page_title':'Customer Deposit',
        'form':form,
    }
    return render(request, 'savings/customer_deposit.html', context)