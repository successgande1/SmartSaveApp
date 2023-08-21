from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib import messages 
import json

# 404 Error Page.
def custom_page_not_found(request, exception=None):
    return render(request, 'accounts/404.html', status=404)

def index(request):
    context = {
        'page_title':"Dashboard"
    }
    return render(request, 'accouns/index.html', context)