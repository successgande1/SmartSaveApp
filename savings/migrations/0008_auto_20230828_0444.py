# Generated by Django 3.2 on 2023-08-28 03:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0007_auto_20230828_0440'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='withdrawalrequest',
            name='approved_by',
        ),
        migrations.RemoveField(
            model_name='withdrawalrequest',
            name='approved_date',
        ),
    ]