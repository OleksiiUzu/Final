# Generated by Django 4.2.7 on 2023-11-11 13:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('money_spending', '0011_rename_product_id_expense_product'),
    ]

    operations = [
        migrations.RenameField(
            model_name='expense',
            old_name='product',
            new_name='product_id',
        ),
    ]
