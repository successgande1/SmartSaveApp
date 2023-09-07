from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect,  get_object_or_404
from.models import Customer, Transaction, WithdrawalRequest, ServiceCharge
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count, Sum
import datetime
from.forms import *
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
import calendar
from django.db.models import Q, F, Subquery, OuterRef
from django.db.models import OuterRef
from django.db.models.functions import Coalesce

# Your view code here


# Your view code here



# Create your views here.
@login_required(login_url='accounts-login')
def create_customer(request):
    # Get the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

   

    logged_user = request.user
    if logged_user.is_authenticated and logged_user.is_superuser or logged_user.profile.role in ['admin']:
        #Get All the Customers
        customers = Customer.objects.order_by('-created_date')[:10]
    elif logged_user.is_authenticated and logged_user.profile.role in ['cashier', 'manager']:
        #Get All the Customers added by the Logged in User
        customers = Customer.objects.filter(added_by=logged_user).order_by('-created_date')[:10]
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

    

    #Check if logged user is admin or super admin
    if request.user.is_superuser or request.user.profile.role in ['admin']:
        #Get List of Customers
        customers = Customer.objects.order_by('-created_date')
        number_of_customers = customers.count()
        #Get Total Account balances of All Customers
        user_customers_deposit_total = Customer.get_total_customers_balance(current_year, current_month)

    #Check if logged user is cahsier or manager 
    elif hasattr(request.user, 'profile') and request.user.profile.role in ['cashier', 'manager']:
        customers = Customer.objects.filter(added_by=request.user).order_by('-created_date')
        number_of_customers = customers.count()
        #Get logged user customers total Deposit for the month
        user_customers_deposit_total = Customer.get_user_total_customer_balance(current_year, current_month, request.user)

    for customer in customers:
        customer.has_pending_withdrawal = customer.set_pending_withdrawal_status()

    form = SearchForm(request.GET or None)

    #search Customers
    if request.method == "GET" and form.is_valid():
        search_query = form.cleaned_data['search_query']
        customers = Customer.objects.filter(
            Q(account_number__icontains=search_query) |
            Q(customer__profile__phone=search_query) |
            Q(customer__profile__full_name__icontains=search_query) 
        )

    
    paginator = Paginator(customers, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Customer List',
        'customers': page_obj,
        'form': form,
        'number_of_customers':number_of_customers, 
        'user_customers_deposit_total':user_customers_deposit_total,
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
            return redirect('transaction-list')
    else:
        form = DepositForm()
    
    context = {
        'customer': customer,
        'page_title': 'Customer Deposit',
        'form': form,
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
        
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
    month_name = calendar.month_name[current_month]
    
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)
   

    #Get Deposits 
    deposits = Transaction.objects.filter(transaction_type='deposit').order_by('-transaction_date')
    if request.user.is_superuser or request.user.profile in ['admin']:  # Admin user
        
        # FILTER DEPOSITED BY THE LOGGED CUSTOMER
        my_today_deposit = Transaction.objects.filter(
            added_by=request.user,
            transaction_type='deposit',
            transaction_date__year=current_year,
            transaction_date__month=current_month
        ).order_by('-transaction_date')

        #Calculate Total DEPOSITED BY LOGGED USER
        my_total_deposits_today = my_today_deposit.aggregate(Sum('amount'))['amount__sum'] or 0.00

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
    
    elif request.user.is_authenticated and request.user.profile.role in ['cashier', 'manager']:  # Manager or Cashier user
       
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
        'my_total_deposits_today':my_total_deposits_today,
        'month_name':month_name,
        
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

    #Check if user is admin or super admin
    if request.user.is_superuser or request.user.profile.role in ['admin'] and request.user.profile.is_active:  # Admin user or Manager
        withdrawal = Transaction.objects.filter(
            transaction_date__year=current_year,
            transaction_date__month=current_month
        ).order_by('-transaction_date')

        #Get all the available properties and sort with slice
        logged_user_transactions = Transaction.objects.all().order_by('-transaction_date')
        
        total_general_withdrawals = withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

    elif request.user.profile.role in ['cashier', 'manager'] and request.user.profile.is_active:  # Cashier user
        #Get Logged in user added Withdrawal 
        logged_user_transactions = Transaction.objects.filter(
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            added_by=request.user  # Assuming the user field is related to the User model
        ).order_by('-transaction_date')

    #Empty Search Logged in user Transaction Form
    form = SearchForm(request.GET or None)
    
    
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
        
    }
    return render(request, 'savings/customer_deposit.html', context)


#Withdrawal Request List view
@login_required(login_url='accounts-login')
def withdrawal_request_list(request):
    current_date = timezone.now()
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year

    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)
    
    #Call Method to calculate Total Amount Requested by logged in User
    my_total_withdrawal_requests_today = WithdrawalRequest.get_total_withdrawal_request_by_user(current_year, current_month, current_day, request.user)
    #Call Method to calculate Total Amount Requested by logged in User
    total_withdrawal_requests_today = WithdrawalRequest.get_total_withdrawal_request(current_year, current_month, current_day)
    
    #Current Month TOTAL PENDING WITHDRAWAL REQUEST
    current_month_pending_requests_total = WithdrawalRequest.get_month_total_withdrawal_request(current_year, current_month)
    
    #Count Number of PENDING REQUEST
    number_pending_request = WithdrawalRequest.objects.filter(is_approved=False).count()

    total_general_withdrawals = 0.00  # Initialize this variable for the scope

    if request.user.is_superuser or request.user.profile.role == 'admin':  # Admin user 
      
        withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month
        ).order_by('-transaction_date')
        
        total_general_withdrawals = withdrawal.aggregate(Sum('amount'))['amount__sum'] or 0.00

        #Filter all Withdrawal request PENDING APPROVAL
        logged_user_withdrawal_request = WithdrawalRequest.objects.filter(
                is_approved=False,
                request_date__year=current_year,
                request_date__month=current_month,
            ).order_by('-request_date')

    elif request.user.profile.role in ['cashier', 'manager']:  # Cashier user
        
        #Current Month TOTAL PENDING WITHDRAWAL REQUEST ADDED BY CASHIER/MANAGER
        current_month_pending_requests_total = WithdrawalRequest.get_cashier_month_total_withdrawal_request(current_year, current_month, request.user)
        
        #Count Number of PENDING REQUEST MADE BY CASHIER/MANAGER
        number_pending_request = WithdrawalRequest.objects.filter(added_by=request.user, is_approved=False).count()

        #Get Logged in user added Withdrawal 
        withdrawal = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            added_by=request.user  # user field is related to the User model
        ).order_by('-transaction_date')

        #Filter all Withdrawal request done by logged in user FOR THE MONTH
        logged_user_withdrawal_request = WithdrawalRequest.objects.filter(
                request_date__year=current_year,
                request_date__month=current_month,
                #request_date__day=current_day,
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
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'current_month_pending_requests_total':current_month_pending_requests_total,
        'total_withdrawal_requests_today':total_withdrawal_requests_today, 
        'total_general_withdrawals': total_general_withdrawals,
        'my_total_withdrawal_requests_today':my_total_withdrawal_requests_today,
        'number_pending_request':number_pending_request,
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
    

    if request.user.is_superuser or request.user.profile.role in ['admin'] and request.user.profile.is_active:  # Admin user
        

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
    
    elif request.user.profile.role in ['cashier', 'manager'] and request.user.profile.is_active:  # Manager or Cashier user
        
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

        charged_customer_count = 0  # Initialize a counter for charged customers

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
                        
                        charged_customer_count += 1  # Increment the charged customer count
                
            except Customer.DoesNotExist:
                pass
        messages.success(request, f'{charged_customer_count} Customer(s) successfully Charged Service Fee.')
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
       

    }
    return render(request, 'savings/process_charge.html', context)

#Customer Statement view
@login_required(login_url='accounts-login')
def customer_statement(request, pk):
    #Get current date, month, year and day
    current_date = timezone.now()
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year
    month_name = calendar.month_name[current_month]

    customer = get_object_or_404(Customer, pk=pk)

    #Call method from Model to calculate Total Deposited by Each Customer this Month
    customer_total_deposited_this_month = Transaction.get_customer_total_desposited_current_month(current_year,current_month,customer)

    #Call method from Model to calculate Total Withdrawn by Each Customer this Month
    customer_total_withdrawn_this_month = Transaction.get_customer_total_withdrawn_current_month(current_year,current_month,customer)
    
    customer_transactions = Transaction.objects.filter(customer=customer,  transaction_date__year=current_year, transaction_date__month=current_month)
    
    form = SearchTransactionForm(request.GET or None)

    if request.method == "GET" and form.is_valid():
        search_query = form.cleaned_data['search_query']
        #Filter Request added by logged in users
        customer_transactions = Transaction.objects.filter(
            
            Q(transaction_ref__icontains=search_query)
        )
    else:
        form = SearchTransactionForm()

    paginator = Paginator(customer_transactions, 5)  # Show 5 Customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    
    context = {
        'form':form,
        'current_year':current_year,
        'month_name':month_name,
        'page_title':'Customer Statement',
        'customer_transactions':page_obj,
        'customer_total_deposited_this_month':customer_total_deposited_this_month,
        'customer_total_withdrawn_this_month':customer_total_withdrawn_this_month,
    }
    return render(request, 'savings/statement.html', context)

#Transaction View Report with Date Range
@login_required(login_url='accounts-login')
def report_types_view(request):
    if request.user.is_superuser or (request.user.profile.role == 'admin' and request.user.profile.is_active):
        if request.method == 'POST':
            form = ReportForm(request.POST)
            if form.is_valid():
                transaction_type = form.cleaned_data['transaction_type']
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                
                # Filter transactions by type and date range
                transactions = Transaction.objects.filter(
                    transaction_type=transaction_type,
                    transaction_date__date__gte=start_date,
                    transaction_date__date__lte=end_date
                )
                
                # Calculate the total amount for the selected type
                total_amount = transactions.aggregate(total_amount=Sum('amount'))['total_amount']
                # Count the number of transactions
                transaction_count = transactions.count()

                paginator = Paginator(transactions, 5)  # Show 5 Transactions per page
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)

                context = {
                    'form': form,
                    'transaction_count': transaction_count,
                    'page_title': 'Transaction Report',
                    'transactions': page_obj,
                    'total_amount': total_amount or 0,
                }
                
                return render(request, 'savings/report_template.html', context)
        else:
            form = ReportForm()
    else:
        return redirect('accounts-login')
    
    context = {'form': form, 'page_title': 'Transaction Report'}
    return render(request, 'savings/report_template.html', context)


#Search Transaction using Date Range by User View
@user_passes_test(lambda u: u.is_superuser or u.profile.role == 'admin', login_url='accounts-login')
def user_transaction_report_view(request):
    if request.method == 'POST':
        form = UserTransactionReportForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user']
            transaction_type = form.cleaned_data['transaction_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Filter transactions by user, type, and date range
            transactions = Transaction.objects.filter(
                added_by_id=user_id,
                transaction_type=transaction_type,
                transaction_date__date__gte=start_date,
                transaction_date__date__lte=end_date
            )
            
            # Calculate the total amount for the selected type
            total_amount = transactions.aggregate(total_amount=Sum('amount'))['total_amount']
            # Count the number of transactions
            transaction_count = transactions.count()

            paginator = Paginator(transactions, 5)  # Show 5 Transactions per page
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            context = {
                'form': form,
                'transaction_count': transaction_count,
                'page_title': 'User Transaction Report',
                'transactions': page_obj,
                'total_amount': total_amount or 0,
            }
            
            return render(request, 'savings/report_template.html', context)
    else:
        form = UserTransactionReportForm()

    context = {'form': form, 'page_title': 'User Transaction Report'}
    return render(request, 'savings/report_template.html', context)

#Printable Report for Admin
@user_passes_test(lambda u: u.is_superuser or u.profile.role == 'admin', login_url='accounts-login')
def generate_admin_report(request):
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            # Calculate summary information
            total_customers = Customer.objects.count()
            total_deposits = Transaction.objects.filter(
                transaction_type='deposit',
                transaction_date__range=(start_date, end_date)
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
            total_withdrawals = Transaction.objects.filter(
                transaction_type='withdraw',
                transaction_date__range=(start_date, end_date)
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
            total_service_charges = ServiceCharge.objects.filter(
                charged_date__range=(start_date, end_date)
            ).aggregate(total_amount=Sum('charged_amount'))['total_amount'] or 0
            net_balance = total_deposits - total_withdrawals - total_service_charges

            # Get customer transactions
            customer_transactions = Transaction.objects.filter(
                transaction_date__range=(start_date, end_date)
            ).order_by('-transaction_date')

            # Get withdrawal requests
            withdrawal_requests = WithdrawalRequest.objects.filter(
                request_date__range=(start_date, end_date)
            ).order_by('-request_date')

            # Get cashier and manager activity
            cashier_manager_activity = Transaction.objects.filter(
                added_by__profile__role__in=['cashier', 'manager'],
                transaction_date__range=(start_date, end_date)
            ).order_by('-transaction_date')

            # Get new customers added within the date range
            new_customers = Customer.objects.filter(
                created_date__range=(start_date, end_date)
            ).count()

            # Calculate total deposits added by each admin, cashier, or manager within the date range
            user_deposits = Transaction.objects.filter(
            transaction_type='deposit',
            transaction_date__range=(start_date, end_date),
            added_by__profile__role__in=['admin', 'cashier', 'manager']
            ).annotate(
                username=F('added_by__username'),
                role=F('added_by__profile__role'),
                full_name=F('added_by__profile__full_name')
            ).values('username', 'role', 'full_name').annotate(total_deposits=Sum('amount'))

            # Calculate total customers added by each staff member
            user_customers = Customer.objects.filter(
                added_by__profile__role__in=['admin', 'cashier', 'manager'],
                created_date__range=(start_date, end_date)
            ).values('added_by__username').annotate(total_customers=Count('id'))

            # Combine both querysets to include total customers in the user_deposits queryset
            user_deposits = user_deposits.annotate(
                total_customers=Coalesce(Subquery(
                    user_customers.filter(added_by__username=OuterRef('username')).values('total_customers')[:1]
                ), 0)
            )

            context = {
                'form': form,
                'user_deposits':user_deposits,
                'start_date': start_date,
                'end_date': end_date,
                'total_customers': total_customers,
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'total_service_charges': total_service_charges,
                'net_balance': net_balance,
                'customer_transactions': customer_transactions,
                'withdrawal_requests': withdrawal_requests,
                'cashier_manager_activity': cashier_manager_activity,
                'new_customers': new_customers,
                'page_title':'Admin Report',
            }

            return render(request, 'savings/admin_report.html', context)
    else:
        form = DateRangeForm()

    context = {'form': form}
    return render(request, 'savings/admin_report.html', context)

#Cashier/Manager Transaction Date Range Report
@user_passes_test(lambda u: u.profile.role == 'cashier' or u.profile.role == 'manager' and u.profile.is_active, login_url='accounts-login')
def staff_transaction_report_view(request):
    if request.method == 'POST':
        form = StaffTransactionDateRangeForm(request.POST)
        if form.is_valid():
            transaction_type = form.cleaned_data['transaction_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Filter transactions by user, type, and date range
            transactions = Transaction.objects.filter(
                transaction_type=transaction_type,
                transaction_date__date__gte=start_date,
                transaction_date__date__lte=end_date,
                added_by = request.user
            )
            
            # Calculate the total amount for the selected type
            total_amount = transactions.aggregate(total_amount=Sum('amount'))['total_amount']
            # Count the number of transactions
            transaction_count = transactions.count()

            paginator = Paginator(transactions, 5)  # Show 5 Transactions per page
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            context = {
                'form': form,
                'transaction_count': transaction_count,
                'page_title': 'Staff Transaction Report',
                'transactions': page_obj,
                'total_amount': total_amount or 0,
            }
            
            return render(request, 'savings/report_template.html', context)
    else:
        form = StaffTransactionDateRangeForm()

    context = {'form': form, 'page_title': 'User Transaction Report'}
    return render(request, 'savings/report_template.html', context)
