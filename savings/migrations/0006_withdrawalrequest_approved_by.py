# Generated by Django 3.2 on 2023-08-28 00:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('savings', '0005_auto_20230826_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='withdrawalrequest',
            name='approved_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='approved_withdrawal_requests', related_query_name='approved_withdrawal_request', to='auth.user'),
            preserve_default=False,
        ),
    ]