# Generated by Django 4.2.7 on 2023-11-09 14:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('money_spending', '0007_alter_productcount_count'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productcount',
            old_name='count',
            new_name='number_of_products',
        ),
    ]
