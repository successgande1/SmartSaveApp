from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib import messages 
import json
from savings.models import Customer, Transaction, WithdrawalRequest
from django.db.models import Count, Sum
import datetime
from savings.forms import *
from django.db.models import Q, F
from .models import Profile
from django.contrib.auth.views import LoginView
from.forms import *
from django.utils import timezone
from django.contrib.auth import login, authenticate
from .helpers import (
    get_profile,
    profile_complete,
)

# 404 Error Page.
def custom_page_not_found(request, exception=None):
    return render(request, 'accounts/404.html', status=404)

# 403 Error Page.
def custom_page_forbidden(request, exception=None):
    return render(request, 'accounts/403.html', status=403)

# 500 Error Page.
def custom_server_not_found(request, exception=None):
    return render(request, 'accounts/500.html', status=500)

#Create User View
@login_required(login_url='accounts-login')
def create_user(request):
    logged_user = request.user
    try:
        user_profile = Profile.objects.get(user=logged_user)
        user_role = user_profile.role
        #Check if logged in user is super admin or admin else don't allow access
        if logged_user.is_superuser or user_role == 'admin':
            if request.method == 'POST':
                form = UserCreationAndRoleForm(request.POST)
                if form.is_valid():
                    user = form.save()
                    role = form.cleaned_data.get('role')
                    # Get or create the user's profile and update the role
                    profile, created = Profile.objects.get_or_create(user=user)
                    profile.role = role
                    profile.save()
                    return redirect('accounts-dashboard')
            else:
                form = UserCreationAndRoleForm()
            context = {
                'page_title': 'Create User',
                'form': form
                }
            return render(request, 'accounts/create_user.html', context)
        else:
            return redirect('accounts-dashboard')
    except Profile.DoesNotExist:
        # Handle the case when the profile doesn't exist
        return redirect('accounts-dashboard')

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            user = authenticate(request, username=username, password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                user_role = Profile.objects.get(user=user).role #Get user role
                if user.is_superuser or user_role == 'admin' or user_role == 'cashier' or user_role == 'manager':
                    return redirect('accounts-dashboard')
                else:
                    messages.warning(request, 'Not Logged In')
                    return redirect('accounts-login')
    else:
        form = CustomAuthenticationForm()

    context = {
        'form': form
        }
    return render(request, 'accounts/login.html', context)


#Dashboard View
@login_required(login_url='accounts-login')
def index(request):
    logged_user = request.user

    if not logged_user.is_authenticated:
        messages.warning(request, 'Not Logged In')
        return redirect('accounts-login')
    
    if logged_user.is_superuser or logged_user.profile.role in ['admin']:
        # Get the current month and year
        current_date = timezone.now()
        current_day = current_date.day
        current_month = current_date.month
        current_year = current_date.year
        #today = datetime.date.today()
        #tomorrow = today + datetime.timedelta(days=1)
        
        # Call the methods in your model to get the total deposits and withdrawals ## 
        total_deposit_today = Transaction.get_total_deposit_today(current_year, current_month, current_day)
        
        total_withdrawal_today = Transaction.get_total_withdrawal_today(current_year, current_month, current_day)
        
        #Call Method to get SUM of withdrawal request Due Tomorrow
        total_withdrawal_request_today = WithdrawalRequest.get_total_withdrawal_request(current_year, current_month, current_day)
        total_deposits = Transaction.get_total_deposits(current_year, current_month)
        total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

        #Count all the available customers
        number_of_customers = Customer.objects.all().count()

        total_customers_balance = Customer.get_total_customers_balance(current_year, current_month)

        #Filter all Withdrawal request done for THE DAY
        count_withdrawal_request_today = WithdrawalRequest.objects.filter(
        is_approved=False,
        request_date__year=current_year,
        request_date__month=current_month,
        request_date__day=current_day
        ).count()

        
        # Count Number of customers who has withdrawn today
        count_withdrawals_today = Transaction.objects.filter(
            transaction_type='withdraw',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            transaction_date__day=current_day
        ).count()

        # Count Number of Customer Deposited today
        count_deposit_today = Transaction.objects.filter(
            transaction_type='deposit',
            transaction_date__year=current_year,
            transaction_date__month=current_month,
            transaction_date__day=current_day
        ).count()

       

        #Get recently registered customers
        customers = Customer.objects.order_by('-created_date')[:5]

        #Get Recent Transactions
        transactions = Transaction.objects.order_by('-transaction_date')[:5]
        #Get Day of today from current date and time
        #date_today = datetime.datetime.now().date
        context = {
            'total_customers_balance':total_customers_balance,
            'total_deposits':total_deposits,
            'total_withdrawals':total_withdrawals,
            'number_of_customers':number_of_customers,
            'total_withdrawal_today':total_withdrawal_today, 
            'current_date':current_date,
            #'tomorrow':tomorrow,
            'page_title':"Dashboard",
            'customers':customers,
            'transactions':transactions,
            'total_deposit_today':total_deposit_today,
            'total_withdrawal_request_today':total_withdrawal_request_today,
            'count_deposit_today':count_deposit_today,
            'count_withdrawals_today':count_withdrawals_today,
            'count_withdrawal_request_today':count_withdrawal_request_today,
        }
        return render(request, 'accounts/index.html', context)
    
    elif logged_user.is_authenticated and logged_user.profile.role in ['cashier', 'manager'] and logged_user.profile.is_active:
        profile = get_profile(logged_user)
        if not profile_complete(profile):
                return redirect('accounts-profile-update')
        else:
             # Get the current month and year
            # Get the current month and year
            current_date = timezone.now()
            current_day = current_date.day
            current_month = current_date.month
            current_year = current_date.year
            # today = datetime.date.today()
            # tomorrow = today + datetime.timedelta(days=1) 
        
            # Call the methods in model to get the total deposits added by logged in user ## 
            user_total_deposit_today = Transaction.get_user_total_desposited_today(current_year, current_month, current_day, request.user)

            # Call the methods in model to get the total deposits added by logged in user ## 
            user_total_withdrawal_today = Transaction.get_user_total_withdrawal_today(current_year, current_month, current_day, request.user)

            # Call the methods in model to get the total deposits added by logged in user ## 
            user_total_withdrawal_request_today = WithdrawalRequest.get_total_withdrawal_request_by_user(current_year, current_month, current_day, request.user)
            
            #Filter all Withdrawal request done for THE DAY
            count_user_withdrawal_request_today = WithdrawalRequest.objects.filter(
            is_approved=False,
            request_date__year=current_year,
            request_date__month=current_month,
            request_date__day=current_day,
            added_by=request.user
            ).count()

            
            # Count Number of customers who has withdrawn today
            count_user_withdrawals_today = Transaction.objects.filter(
                transaction_type='withdraw',
                transaction_date__year=current_year,
                transaction_date__month=current_month,
                transaction_date__day=current_day,
                added_by=request.user
            ).count()

            # Count Number of Customer Deposited today
            count_user_deposit_today = Transaction.objects.filter(
                transaction_type='deposit',
                transaction_date__year=current_year,
                transaction_date__month=current_month,
                transaction_date__day=current_day,
                added_by=request.user
            ).count()
                
            
            
            # Call the methods in your model to get the total deposits and withdrawals 
            total_deposits = Transaction.get_total_deposits(current_year, current_month)
            total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)
            
            #Get Day of today from current date and time
            # date_today = datetime.datetime.now().date
            #Get recently registered customers
            customers = Customer.objects.filter(added_by=request.user).order_by('-created_date')[:5]
             #Get Recent Transactions
            transactions = Transaction.objects.filter(added_by=request.user).order_by('-transaction_date')[:5]
             
             
        context = {
            # 'date_today':date_today,
            'page_title':"Dashboard",
            'customers':customers,
            'transactions':transactions,
            'total_deposits':total_deposits,
            'total_withdrawals':total_withdrawals,
           
            'user_total_deposit_today':user_total_deposit_today,
            'current_date':current_date,
            'user_total_withdrawal_today':user_total_withdrawal_today,
            'user_total_withdrawal_request_today':user_total_withdrawal_request_today,
            #'tomorrow':tomorrow,
            'count_user_deposit_today':count_user_deposit_today,
            'count_user_withdrawals_today':count_user_withdrawals_today,
            'count_user_withdrawal_request_today':count_user_withdrawal_request_today,
        }
        
        return render(request, 'accounts/index.html', context)
    
    elif logged_user.is_authenticated and not hasattr(logged_user, 'profile'):
        date_today = datetime.datetime.now().date
        context = {
            'date_today':date_today,
            'page_title':"Dashboard",
        }
        return render(request, 'accounts/index.html', context)
         
    else:
        messages.warning(request, 'No User Found')
        return redirect('accounts-login')


             
#Update Profile Method
@login_required(login_url='accounts-login')
def profile_update(request):
    # Get the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year
        
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

   

    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, 
        instance=request.user.profile)
        #Check if both forms are valid
        if  profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your Profile Updated Successfully')
            return redirect('accounts-profile')
    else:
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
            'profile_form': profile_form,
            'total_deposits':total_deposits,
            'total_withdrawals':total_withdrawals,
            
        }
    return render(request, 'accounts/update_profile.html', context)
    
#User Profile
@login_required(login_url='accounts-login')
def profile(request):
    # Get the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year
        
    # Call the methods in your model to get the total deposits and withdrawals
    total_deposits = Transaction.get_total_deposits(current_year, current_month)
    total_withdrawals = Transaction.get_total_withdrawals(current_year, current_month)

   

    context = {
        'page_title':'Profile Detail',
        'total_deposits':total_deposits,
        'total_withdrawals':total_withdrawals,
       
    }
    return render(request, 'accounts/profile.html', context)

@login_required(login_url='accounts-login')
def staff_list(request):
    if request.user.is_superuser or request.user.profile.role in ['admin']:
        #List of Staff
        staff_list = Profile.objects.filter(Q(role="cashier") | Q(role="manager") | Q(role="admin")).order_by('-last_updated')
        number_of_staff = staff_list.count()

    form = SearchForm(request.GET or None)

    if request.method == "GET" and form.is_valid():
        search_query = form.cleaned_data['search_query']
        #Filter staff users
        staff_list = Profile.objects.filter(
            Q(user__username__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(full_name__icontains=search_query),
            Q(role='cashier') | Q(role='manager') | Q(role='admin') 
        )

    paginator = Paginator(staff_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title':'List of Staff',
        'staff_list':page_obj,
        'number_of_staff':number_of_staff,
        'form':form, 
    }
    return render(request, 'accounts/staff_list.html', context)


#Disable user
@login_required(login_url='accounts-login')
def disable_user(request, pk):
    if request.user.is_superuser or request.user.profile.role in ['admin']:
        user_to_disable = get_object_or_404(Profile, pk=pk)
        #Change the USER is_active to False
        user_to_disable.is_active = False
        user_to_disable.save()
        messages.error(request, f'{user_to_disable.user.username} Disabled Successfully.')
        return redirect('accounts-staff-list')
    
#Enable User
@login_required(login_url='accounts-login')
def enable_user(request, pk):
    if request.user.is_superuser or request.user.profile.role in ['admin']:
        user_to_enable = get_object_or_404(Profile, pk=pk)
        #Change the USER is_active to False
        user_to_enable.is_active = True
        user_to_enable.save()
        messages.success(request, f'{user_to_enable.user.username} Enabled Successfully.')
        return redirect('accounts-staff-list')
    
#Change user password view
@login_required(login_url='accounts-login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = authenticate(username=request.user.username, password=form.cleaned_data['old_password'])
            if user is not None:
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                update_session_auth_hash(request, user)  # Update session to prevent logout
                messages.success(request, 'Your Password Changed Successfully.')
                return redirect('accounts-password-change-done')  # Redirect to password change success page
            else:
                form.add_error('old_password', 'Incorrect old password')
                messages.warning(request, 'Incorrect old Password.')
    else:
        form = PasswordChangeForm()

    context = {
        'form': form,
        'page_title': 'Change Password',
        }
    return render(request, 'accounts/password_change.html', context)

#Change user password successfully view
@login_required(login_url='accounts-login')
def password_change_done(request):

    context = {
        'page_title':'Password Changed',
    }
    return render(request, 'accounts/password_change_done.html', context)
