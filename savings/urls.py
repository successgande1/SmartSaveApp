from django.urls import path
from . import views


urlpatterns = [
    path('create/account/', views.create_customer, name = 'savings-account'),
    path('customer/list/', views.customer_list, name = 'customer-list'),
    path('customer/statement/<int:pk>/', views.customer_statement, name='customer_statement'),
    path('transaction/list/', views.transaction_list, name = 'transaction-list'),
    path('customer/deposit/<int:pk>/', views.customer_deposit, name='customer_deposit'),
    #path('customer-deposit/<int:pk>/confirm/', views.confirm_deposit, name='confirm-deposit'),
    path('withdrawal/request/<int:pk>/', views.withdrawal_request, name='withdrawal_request'),
    path('request/list/', views.withdrawal_request_list, name = 'request-list'),
    path('withdrawal/approve/<uuid:request_ref>/', views.withdrawal_approval, name='withdrawal_approval'),
    path('deposit/list/', views.deposit_list, name = 'deposit-list'),
    path('withdrawal/list/', views.withdrawal_list, name = 'withdrawal-list'),
    path('process-service-charge/', views.process_service_charge, name='process_service_charge'),
    path('charged-customers/list/', views.list_charged_customers, name='charged_customers_list'), 
]
