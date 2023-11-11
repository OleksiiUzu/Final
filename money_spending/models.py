# models.py
from django.db import models
from django.contrib.auth.models import User


class Limits(models.Model):
    product_name = models.CharField(max_length=200, null=True)
    product_amount = models.DecimalField(max_digits=10, decimal_places=2)
    limit = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    end_limit_date = models.DateTimeField()
    description = models.CharField(max_length=200, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class ProductCount(models.Model):
    number_of_products = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    product_id = models.ForeignKey(Limits, on_delete=models.CASCADE)


class Expense(models.Model):
    date = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, null=False)
    product_id = models.DecimalField(max_digits=10, decimal_places=2, null=True,)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
