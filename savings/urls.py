from django.urls import path
from . import views


urlpatterns = [
    path('create/account/', views.create_customer, name = 'savings-account'),
    path('customer/list/', views.customer_lsit, name = 'customer-list'),
    path('customer/deposit/<int:pk>/', views.customer_deposit, name='customer_deposit'),
]
