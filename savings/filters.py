import django_filters
from .models import Customer, Transaction

class TransactionFilter(django_filters.FilterSet):
    class Meta:
        model = Transaction
        fields = {
            'customer': ['exact'],
            'transaction_ref': ['exact'],
        }

class CustomerFilter(django_filters.FilterSet):
    class Meta:
        model = Customer
        fields = {
            'customer': ['exact'],
            'account_number': ['exact'],
        }
