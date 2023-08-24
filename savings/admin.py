from django.contrib import admin
from . models import *
# Register your models here.

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer', 'account_number', 'account_balance', 'service_charge', 'added_by', 'created_date')
    list_per_page = 6
admin.site.register(Customer, CustomerAdmin)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'transaction_type', 'transaction_ref', 'added_by', 'transaction_remark', 'transaction_date')
    list_per_page = 6
admin.site.register(Transaction, TransactionAdmin)


class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'added_by', 'request_ref', 'is_approved')
    list_per_page = 6
admin.site.register(WithdrawalRequest, WithdrawalRequestAdmin)

class ServiceChargeAdmin(admin.ModelAdmin):
    list_display = ('charged_customer', 'charged_amount', 'charged_date')
    list_per_page = 6
admin.site.register(ServiceCharge, ServiceChargeAdmin)