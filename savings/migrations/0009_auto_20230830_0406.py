# Generated by Django 3.2 on 2023-08-30 03:06

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0008_auto_20230828_0444'),
    ]

    operations = [
        migrations.AddField(
            model_name='withdrawalrequest',
            name='request_date_local',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='withdrawalrequest',
            name='request_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
