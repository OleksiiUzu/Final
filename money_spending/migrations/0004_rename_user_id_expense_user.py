# Generated by Django 4.2.7 on 2023-11-05 08:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('money_spending', '0003_expense_user_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='expense',
            old_name='user_id',
            new_name='user',
        ),
    ]