from django.urls import path
from . import views


urlpatterns = [
    path('create/account/', views.create_customer, name = 'savings-account'),
    path('customer/list/', views.customer_list, name = 'customer-list'),
    path('transaction/list/', views.transaction_list, name = 'transaction-list'),
    path('customer/deposit/<int:pk>/', views.customer_deposit, name='customer_deposit'),
    path('deposit/list/', views.deposit_list, name = 'deposit-list'),
]
