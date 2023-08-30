from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,  get_object_or_404
from.models import Customer, Transaction, WithdrawalRequest, ServiceCharge
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count, Sum
import datetime
from.forms import *
from django.http import JsonResponse
from django.db.models import Q, F
from datetime import timedelta
from django.utils import timezone


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
def customer_list(request):
    customers = Customer.objects.order_by('-created_date')
    form = SearchForm(request.GET or None)

    if request.method == "GET" and form.is_valid():
        search_query = form.cleaned_data['search_query']
        customers = Customer.objects.filter(
            Q(account_number__icontains=search_query) |
            Q(customer__profile__phone=search_query) |
            Q(customer__profile__full_name__icontains=search_query)
        )

    for customer in customers: #Call the function that checks if customer has pending withdrawal
        customer.has_pending_withdrawal = customer.set_pending_withdrawal_status()

    paginator = Paginator(customers, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Customer List',
        'customers': page_obj,
        'form': form,
    }
    return render(request, 'savings/customer_list.html', context)



#Customer Deposit View
@login_required(login_url='accounts-login')
def customer_deposit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            deposit_amount = form.cleaned_data['amount']

            # Create a deposit transaction
            transaction = Transaction.objects.create(
                customer=customer,
                amount=deposit_amount,
                transaction_type='deposit',
                added_by=request.user,
                transaction_remark='Customer Deposit',
                transaction_date=timezone.now()
            )

            messages.success(request, f'N{deposit_amount} Deposited Successfully for Acct. No:{customer.account_number}')
            return redirect('deposit-list')
    else:
        form = DepositForm()
    
    context = {
        'customer': customer,
        'page_title': 'Customer Deposit',
        'form': form,
    }
    return render(request, 'savings/customer_deposit.html', context)

#Customer Deposit List
@login_required(login_url='accounts-login')
def deposit_list(request):
    #Get Deposits
    deposits = Transaction.objects.filter(transaction_type='deposit').order_by('-transaction_date')
    
    paginator = Paginator(deposits, 5)  # Show 5 Desposits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_title':'Deposit List',
        'deposit_withdrawals':page_obj,
    }
    return render(request, 'savings/deposit_withdraw_list.html', context)

#Transactions
@login_required(login_url='accounts-login')
def transaction_list(request):
    
    #Get all the available properties and sort with slice
    transactions = Transaction.objects.order_by('-transaction_date')
    

    form = SearchForm(request.GET or None)

    if request.method == "GET" and form.is_valid():
        search_query = form.cleaned_data['search_query']
        transactions = Transaction.objects.filter(
            Q(customer__account_number=search_query) |
            Q(customer__customer__profile__phone=search_query) |
            Q(transaction_ref__icontains=search_query) |
            Q(customer__customer__profile__full_name__icontains=search_query)
        ) 
    

    paginator = Paginator(transactions, 5)  # Show 5 Transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions':page_obj,
        'form':form,
        'page_title':'Transactions',
        
    }
    return render(request, 'savings/transaction_list.html', context)

#Withdrawal Request view
@login_required(login_url='accounts-login')
def withdrawal_request(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = WithdrawalRequestForm(customer=customer, data=request.POST)
        if form.is_valid():
            withdrawal_request = form.save(commit=False)
            withdrawal_request.customer = customer  # Set the customer before saving
            withdrawal_request.added_by = request.user # Get the logged in user before saving
            withdrawal_request.request_date = timezone.localtime()  # Set the request date to the current local time
            withdrawal_request.save()
            amount = form.cleaned_data['amount']
            messages.success(request, f'Withdrawal Request of N{amount} on Acct. No:{customer.account_number} ')
            return redirect('request-list')
    else:
        form = WithdrawalRequestForm(customer=customer)

    context = {
        'customer': customer,
        'page_title': 'Withdrawal Request',
        'form': form,
    }
    return render(request, 'savings/customer_deposit.html', context)


#Withdrawal Request List view
@login_required(login_url='accounts-login')
def withdrawal_request_list(request):
    
    # Calculate the time threshold in local time
    time_threshold = timezone.localtime() - timedelta(days=1)
    
    customer_request = WithdrawalRequest.objects.filter(
        is_approved=False 
    )
    
    form = SearchForm(request.GET or None)

    if request.method == "GET" and form.is_valid():
        search_query = form.cleaned_data['search_query']
        customer_request = WithdrawalRequest.objects.filter(
            Q(customer__account_number=search_query) |
            Q(customer__customer__profile__phone=search_query) |
            Q(customer__customer__profile__full_name__icontains=search_query) 
        )

    paginator = Paginator(customer_request, 5)  # Show 5 customer_request per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    context = {
        'customers':page_obj,
        'page_title': 'Request List',
        'form':form,  
        'time_threshold': True,
    }
    return render(request, 'savings/transaction_list.html', context)

#Approve and Withdraw Customer Deposit View
@login_required(login_url='accounts-login')
def withdrawal_approval(request, request_ref):
    withdrawal_request = get_object_or_404(WithdrawalRequest, request_ref=request_ref, is_approved=False)

    # Check if the request was made in the last 24 hours
    if withdrawal_request.request_date <= timezone.now() - timedelta(days=1):
        withdrawal_request.is_approved = True
        withdrawal_request.save()

        # Create a withdrawal transaction
        transaction = Transaction.objects.create(
            customer=withdrawal_request.customer,
            amount=withdrawal_request.amount,
            transaction_type='withdraw',
            added_by=request.user,
            transaction_remark='Withdrawal Approval',
            transaction_date=timezone.now()
        )

        messages.success(request, f'Successfully Withdrawn N{withdrawal_request.amount} from Acct. No:{withdrawal_request.customer.account_number}.')
        return redirect('transaction-list')
    else:
        messages.error(request, 'Withdrawal Request was not made within the last 24 Hours')
        return redirect('request-list')
    
#Withdrawal List View
@login_required(login_url='accounts-login')
def withdrawal_list(request):
    withdrawal = Transaction.objects.filter(transaction_type='deposit').order_by('-transaction_date')
    
    paginator = Paginator(withdrawal, 5)  # Show 5 Desposits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title':'Withdrawal List',
        'deposit_withdrawals':page_obj,
    }
    return render(request, 'savings/deposit_withdraw_list.html', context)

    
#Process Service Charge View
@login_required(login_url='accounts-login')
def process_service_charge(request):
    if request.method == 'POST':
        selected_customer_ids = request.POST.getlist('selected_customers')

        for customer_id in selected_customer_ids:
            try:
                customer = Customer.objects.get(id=customer_id)
                
                # Check if the customer's account balance is greater than zero
                if customer.account_balance > 0:
                    # Check if the customer has been charged for the current month
                    service_charge_record = customer.servicecharge_set.filter(charged_date__month=timezone.now().month).first()
                    if service_charge_record is None:
                        service_charge = customer.service_charge

                        # Deduct the service charge from customer's account balance
                        customer.update_account_balance(service_charge)

                        # Create a transaction record for the service charge deduction
                        transaction = Transaction.objects.create(
                            customer=customer,
                            amount=service_charge,
                            transaction_type='service_charge',
                            added_by=request.user,
                            transaction_remark='Service Charge Deduction'
                        )

                        # Create a service charge record
                        service_charge_record = ServiceCharge.objects.create(
                            charged_customer=customer,
                            charged_amount=service_charge,
                            charged_date=timezone.now().date()
                        )
                
            except Customer.DoesNotExist:
                pass

        return redirect('list_customers')  # Redirect to the customer list after processing

    # Fetch eligible customers
    eligible_customers = Customer.objects.filter(
        account_balance__gt=0,
        servicecharge__isnull=True
    )

    paginator = Paginator(eligible_customers, 5)  # Show 5 Customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'eligible_customers': page_obj,
        'page_title': 'Charge Customer Fee',
    }
    return render(request, 'savings/process_charge.html', context)

