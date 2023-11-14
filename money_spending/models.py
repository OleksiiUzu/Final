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

    class Meta:
        app_label = 'money_spending'


class ProductCount(models.Model):
    number_of_products = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    product_id = models.ForeignKey(Limits, on_delete=models.CASCADE)

    class Meta:
        app_label = 'money_spending'


class Expense(models.Model):
    date = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, null=False)
    product_id = models.DecimalField(max_digits=10, decimal_places=2, null=True,)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        app_label = 'money_spending'


class TelegramChatID(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username
