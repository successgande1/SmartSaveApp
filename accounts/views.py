from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib import messages 
import json
from savings.models import Customer, Transaction
from django.db.models import Count, Sum
import datetime
from .models import Profile
from django.contrib.auth.views import LoginView
from.forms import *
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
    
    if logged_user.is_superuser:
        #Get recently registered customers
        customers = Customer.objects.order_by('-created_date')[:5]

        #Get Recent Transactions
        transactions = Transaction.objects.order_by('-transaction_date')[:5]
        #Get Day of today from current date and time
        date_today = datetime.datetime.now().date
        context = {
            'date_today':date_today,
            'page_title':"Dashboard",
            'customers':customers,
            'transactions':transactions,
        }
        return render(request, 'accounts/index.html', context)
    
    elif logged_user.is_authenticated and hasattr(logged_user, 'profile'):
        profile = get_profile(logged_user)
        if not profile_complete(profile):
                return redirect('accounts-profile-update')
        else:
             #Get Day of today from current date and time
             date_today = datetime.datetime.now().date
             #Get recently registered customers
             customers = Customer.objects.filter(added_by=request.user).order_by('-created_date')[:5]
             #Get Recent Transactions
             transactions = Transaction.objects.filter(added_by=request.user).order_by('-transaction_date')[:5]
             
             
        context = {
            'date_today':date_today,
            'page_title':"Dashboard",
            'customers':customers,
            'transactions':transactions,
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
        }
    return render(request, 'accounts/update_profile.html', context)
    
#User Profile
@login_required(login_url='cashier-login')
def profile(request):
    context = {
        'page_title':'Profile Detail'
    }
    return render(request, 'accounts/profile.html', context)