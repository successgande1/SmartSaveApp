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
    # Get the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

    # Calculate the deposited balance
    deposited_balance = total_deposits - total_withdrawals

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
        'form': form,
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        'deposited_balance':deposited_balance,
        }
    return render(request, 'savings/create_customer_account.html', context)

#Customer List View
@login_required(login_url='accounts-login')
def customer_list(request):
    # Get the current month and year
    current_date = timezone.now()
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year
    
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)


    #Check if logged user is admin or super admin
    if request.user.is_superuser or request.user.profile.role == 'admin':
        #Get List of Customers
        customers = Customer.objects.order_by('-created_date')

        #Get Total Account balances of All Customers
        logged_user_customer_deposit_total = Customer.get_total_customers_balance(current_year, current_month)

    #Check if logged user is admin or super admin 
    elif request.user.profile.role == 'cashier' or request.user.profile == 'manager':
        customers = Customer.objects.filter(added_by=request.user).order_by('-created_date')
        
        #Get logged user customers total Deposit for the month
        logged_user_customer_deposit_total = Customer.get_user_total_customer_balance(current_year, current_month, request.user)


    form = SearchForm(request.GET or None)

    #Check Customers
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
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        'logged_user_customer_deposit_total':logged_user_customer_deposit_total,
    }
    return render(request, 'savings/customer_list.html', context)



#Customer Deposit View
@login_required(login_url='accounts-login')
def customer_deposit(request, pk):
    # Get the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

    # Calculate the deposited balance
    deposited_balance = total_deposits - total_withdrawals

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
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        'deposited_balance':deposited_balance,
    }
    return render(request, 'savings/customer_deposit.html', context)

#Customer Deposit List
@login_required(login_url='accounts-login')
def deposit_list(request):
    #Get current date, month, year and day
    current_date = timezone.now()
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year
    
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)
    # total_deposit_today = Transaction.get_total_deposit_today(current_year, current_month, current_day)
    # total_withdrawal_today = Transaction.get_total_withdrawal_today(current_year, current_month, current_day)
    # total_request_today = WithdrawalRequest.get_total_withdrawal_request(current_year, current_month, current_day)

    # Calculate the deposited balance
    deposited_balance = total_deposits - total_withdrawals

    #Get Deposits
    deposits = Transaction.objects.filter(transaction_type='deposit').order_by('-transaction_date')
    if request.user.is_superuser:  # Admin user
        

        # Calculate the deposited balance
        deposited_balance = total_deposits - total_withdrawals

        # General Withdrawal List
        withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month
        ).order_by('-transaction_date')
        
        #Calculate Total Withdrawals
        total_withdrawals = withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

        #Filter all Withdrawal request done for THE DAY
        customer_request = WithdrawalRequest.objects.filter(
        is_approved=False,
        request_date__year=current_year,
        request_date__month=current_month,
        request_date__day=current_day
        )

        # Calculate Total withdrawal Request for THE DAY
        total_withdrawal_request = customer_request.aggregate(Sum('amount'))['amount__sum'] or 0.00
    
    else:  # Manager or Cashier user
        # Calculate the deposited balance
        deposited_balance = total_deposits - total_withdrawals

        # Filter withdrawals for the current user for the DAY
        my_today_withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            transaction_date__day=current_day, 
            added_by=request.user  # Assuming the user field is related to the User model
        ).order_by('-transaction_date')

        # Filter Deposit for the current user for the DAY
        my_today_deposit = Transaction.objects.filter(
            transaction_type='deposit',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            transaction_date__day=current_day, 
            added_by=request.user  # Assuming the user field is related to the User model
        )

        #Filter all Withdrawal request done by logged in user FOR THE DAY
        withdrawal = WithdrawalRequest.objects.filter(
            request_date__year=current_year,
            request_date__month=current_month,
            request_date__day=current_day,
            added_by=request.user # Assuming Customer is related to the User model
        ).order_by('-request_date')

        #Call Method to calculate Total Amount Requested by logged in User
        my_total_withdrawal_requests_today = WithdrawalRequest.get_total_withdrawal_request(current_year, current_month, current_day)
        
        # Calculate Total withdrawal for the CURRENT MONTH related to the logged in user
        total_withdrawals = withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

        # Calculate Total withdrawal for the DAY related to the logged in user
        my_total_withdrawal_today = my_today_withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

        # Calculate Total Deposited for the DAY related to the logged in user
        my_total_deposits_today = my_today_deposit.aggregate(Sum('amount'))['amount__sum'] or 0.00

        
    
    paginator = Paginator(my_today_deposit, 5)  # Show 5 Desposits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_title':'My Deposits Today',
        'my_deposits':page_obj,
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        'deposited_balance':deposited_balance,
        'my_total_deposits_today':my_total_deposits_today,
        'my_total_withdrawal_requests_today':my_total_withdrawal_requests_today,
        'my_total_withdrawal_today':my_total_withdrawal_today,
    }
    return render(request, 'savings/deposit_list.html', context)

#Transactions
@login_required(login_url='accounts-login')
def transaction_list(request):
    # Get the current month and year
    current_date = timezone.now()
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year
    
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

    # Calculate the deposited balance
    deposited_balance = total_deposits - total_withdrawals
    
    #Get all the available properties and sort with slice
    transactions = Transaction.objects.order_by('-transaction_date')

    if request.user.is_superuser:  # Admin user or Manager
        withdrawal = Transaction.objects.filter(
            transaction_date__year=current_year,
            transaction_date__month=current_month
        ).order_by('-transaction_date')
        
        total_general_withdrawals = withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

    else:  # Cashier user
        #Get Logged in user added Withdrawal 
        logged_user_transactions = Transaction.objects.filter(
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            added_by=request.user  # Assuming the user field is related to the User model
        ).order_by('-transaction_date')

    #Empty Search Logged in user Transaction Form
    form = SearchForm(request.GET or None)
    #Filter all Transactions done by logged in user FOR THE DAY
    logged_user_transactions = Transaction.objects.filter(
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            transaction_date__day=current_day,
            added_by=request.user # Assuming Customer is related to the User model
    ).order_by('-transaction_date')
    
    #Empty Search Logged in user Transaction Form
    if request.method == "GET" and form.is_valid():
        search_query = form.cleaned_data['search_query']
        logged_user_transactions = Transaction.objects.filter(
            Q(customer__account_number=search_query) |
            Q(customer__customer__profile__phone=search_query) |
            Q(transaction_ref__icontains=search_query) |
            Q(customer__customer__profile__full_name__icontains=search_query)
        ) 
    

    paginator = Paginator(logged_user_transactions, 5)  # Show 5 Transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'logged_user_transactions':page_obj,
        'form':form,
        'page_title':'Transactions',
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        'deposited_balance':deposited_balance,
    }
    return render(request, 'savings/transaction_list.html', context)

#Withdrawal Request view
@login_required(login_url='accounts-login')
def withdrawal_request(request, pk):
    # Get the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

    # Calculate the deposited balance
    deposited_balance = total_deposits - total_withdrawals

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
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        'deposited_balance':deposited_balance,
    }
    return render(request, 'savings/customer_deposit.html', context)


#Withdrawal Request List view
@login_required(login_url='accounts-login')
def withdrawal_request_list(request):
    current_date = timezone.now()
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year

    #Determine current time in the local time zone with a duration of one day ago 
    time_threshold = timezone.localtime() - timedelta(days=1)

    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)
    total_withdrawal_today = Transaction.get_total_withdrawal_today(current_year, current_month, current_day)
    #Call Method to calculate Total Amount Requested by logged in User
    my_total_withdrawal_requests_today = WithdrawalRequest.get_total_withdrawal_request_by_user(current_year, current_month, current_day, request.user)
    #Call Method to calculate Total Amount Requested by logged in User
    total_withdrawal_requests_today = WithdrawalRequest.get_total_withdrawal_request(current_year, current_month, current_day)
    
    total_general_withdrawals = 0.00  # Initialize this variable for the scope

    if request.user.is_superuser or request.user.profile.role == 'admin':  # Admin user 
        

        deposited_balance = total_deposits - total_withdrawals

        withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month
        ).order_by('-transaction_date')
        
        total_general_withdrawals = withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

        customer_request = WithdrawalRequest.objects.filter(
            is_approved=False,
            request_date__year=current_year,
            request_date__month=current_month,
            request_date__day=current_day
        )

        #Filter all Withdrawal request done by logged in user FOR THE DAY
        logged_user_withdrawal_request = WithdrawalRequest.objects.filter(
                request_date__year=current_year,
                request_date__month=current_month,
                request_date__day=current_day
            ).order_by('-request_date')

    else:  # Cashier user
        
        deposited_balance = total_deposits - total_withdrawals
        
        #Get Logged in user added Withdrawal 
        withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            added_by=request.user  # Assuming the user field is related to the User model
        ).order_by('-transaction_date')

        #Filter all Withdrawal request done by logged in user FOR THE DAY
        logged_user_withdrawal_request = WithdrawalRequest.objects.filter(
                request_date__year=current_year,
                request_date__month=current_month,
                request_date__day=current_day,
                added_by=request.user # Assuming Customer is related to the User model
        ).order_by('-request_date')

        
        
        

    

    form = SearchForm(request.GET or None)

    if request.method == "GET" and form.is_valid():
        search_query = form.cleaned_data['search_query']
        #Filter Request added by logged in users
        logged_user_withdrawal_request = WithdrawalRequest.objects.filter(
            Q(customer__account_number=search_query) |
            Q(customer__customer__profile__phone=search_query) |
            Q(customer__customer__profile__full_name__icontains=search_query)
        )

    paginator = Paginator(logged_user_withdrawal_request, 5)  # Show 5 customer_request per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'customers': page_obj,
        'page_title': 'Request List',
        'form': form,
        'time_threshold': True,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'deposited_balance': deposited_balance,
        'total_withdrawal_requests_today':total_withdrawal_requests_today, 
        'total_general_withdrawals': total_general_withdrawals,
        'my_total_withdrawal_requests_today':my_total_withdrawal_requests_today,
    }
    return render(request, 'savings/withdrawal_request_list.html', context)




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
    #Get current date, month, year and day
    current_date = timezone.now()
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year

    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)
    total_deposit_today = Transaction.get_total_deposit_today(current_year, current_month, current_day)
    

    if request.user.is_superuser:  # Admin user
        

        # Calculate the deposited balance
        deposited_balance = total_deposits - total_withdrawals

        # General Withdrawal List
        withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month
        ).order_by('-transaction_date')
        
        #Calculate Total Withdrawals
        total_withdrawals = withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

        #Filter all Withdrawal request done for THE DAY
        customer_request = WithdrawalRequest.objects.filter(
        is_approved=False,
        request_date__year=current_year,
        request_date__month=current_month,
        request_date__day=current_day
        )

        # Calculate Total withdrawal Request for THE DAY
        total_withdrawal_request = customer_request.aggregate(Sum('amount'))['amount__sum'] or 0.00
    
    else:  # Manager or Cashier user
        # Call the methods in the Transaction model to get the total deposits and withdrawals
        # total_deposits = Transaction.get_total_deposits(current_year, current_month)
        # total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)
        # total_deposit_today = Transaction.get_total_deposit_today(current_year, current_month, current_day)
        # total_withdrawal_today = Transaction.get_total_withdrawal_today(current_year, current_month, current_day)
        # total_request_today = WithdrawalRequest.get_total_withdrawal_request(current_year, current_month, current_day)

        # Calculate the deposited balance
        deposited_balance = total_deposits - total_withdrawals
        # Filter withdrawals for the current user for the current Month
        withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            added_by=request.user  # Assuming the user field is related to the User model
        ).order_by('-transaction_date')

        # Filter withdrawals for the current user for the DAY
        my_today_withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            transaction_date__day=current_day, 
            added_by=request.user  # Assuming the user field is related to the User model
        ).order_by('-transaction_date')

        # Filter Deposit for the current user for the DAY
        today_deposit = Transaction.objects.filter(
            transaction_type='deposit',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            transaction_date__day=current_day, 
            added_by=request.user  # Assuming the user field is related to the User model
        )

        #Filter all Withdrawal request done by logged in user FOR THE DAY
        withdrawal = WithdrawalRequest.objects.filter(
            request_date__year=current_year,
            request_date__month=current_month,
            request_date__day=current_day,
            added_by=request.user # Assuming Customer is related to the User model
        ).order_by('-request_date')

        #Call Method to calculate Total Amount Requested by logged in User
        my_total_withdrawal_requests_today = WithdrawalRequest.get_total_withdrawal_request(current_year, current_month, current_day)
        
        # Calculate Total withdrawal for the CURRENT MONTH related to the logged in user
        total_withdrawals = withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

        # Calculate Total withdrawal for the DAY related to the logged in user
        my_total_withdrawal_today = my_today_withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

        # Calculate Total Deposited for the DAY related to the logged in user
        my_total_deposits_today = today_deposit.aggregate(Sum('amount'))['amount__sum'] or 0.00

    
    paginator = Paginator(my_today_withdrawal, 5)  # Show 5 Desposits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title':'Withdrawal List',
        'withdrawals':page_obj,
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        'deposited_balance':deposited_balance,
        'my_total_withdrawal_today':my_total_withdrawal_today,
        'my_total_deposits_today':my_total_deposits_today,
        'total_deposit_today':total_deposit_today,
        'my_total_withdrawal_requests_today':my_total_withdrawal_requests_today,
        
    }
    return render(request, 'savings/withdrawal_list.html', context)

    

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
        messages.success(request, 'Customers Charged Service Fee successfully.')
        return redirect('charged_customers_list')  # Redirect to the customer list after processing

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
        'page_title': 'Process Service Charge',
    }
    return render(request, 'savings/process_charge.html', context)

#Charged Customers list Views
@login_required(login_url='accounts-login')
def list_charged_customers(request):
    # Get the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year

    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

    # Calculate the deposited balance
    deposited_balance = total_deposits - total_withdrawals

    
    # Calculate the sum of charged_amount for the current month
    charged_amount_sum = ServiceCharge.objects.filter(
        charged_date__month=current_month,
        charged_date__year=current_year
    ).aggregate(Sum('charged_amount'))['charged_amount__sum'] or 0.00
    
    # Get all charged customers for the current month
    charged_customers = ServiceCharge.objects.filter(
        charged_date__month=current_month,
        charged_date__year=current_year
    )
    
    paginator = Paginator(charged_customers, 5)  # Show 5 Customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Charged Customers',
        'charged_amount_sum': charged_amount_sum,
        'eligible_customers': page_obj,
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        'deposited_balance':deposited_balance,
        # 'total_requested_amount':total_requested_amount,

    }
    return render(request, 'savings/process_charge.html', context)