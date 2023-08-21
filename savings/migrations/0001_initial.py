# Generated by Django 3.2 on 2023-08-21 15:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_number', models.CharField(max_length=10, null=True)),
                ('account_balance', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('added_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_customer', to=settings.AUTH_USER_MODEL)),
                ('customer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WithdrawalRequest',
            fields=[
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('request_ref', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_approved', models.BooleanField(default=False)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='added_withdrawal_requests', related_query_name='added_withdrawal_request', to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='savings.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_type', models.CharField(blank=True, max_length=16)),
                ('transaction_ref', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transaction_remark', models.CharField(blank=True, max_length=100)),
                ('transaction_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='added_transactions', related_query_name='added_transaction', to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='savings.customer')),
            ],
        ),
    ]