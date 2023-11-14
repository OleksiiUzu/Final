import asyncio
import base64
import collections

from datetime import datetime

import telebot
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from money_spending.templatetags.filters import get_item  # custom filter for templates
from money_spending.models import Expense, Limits, ProductCount, TelegramChatID
from money_spending.utils import (money_amount_validation,
                                  convert_amount,
                                  chart_calculation,
                                  product_limits_calculation,
                                  adding_money,
                                  get_products_left,
                                  group_histogram,
                                  time_range_expenses)
from django.middleware.csrf import get_token
from django.http import JsonResponse

# add rise or sand message


def index(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')
    return render(request, 'index.html')


def expenses_chart(request):
    if request.method == "POST":
        post_data = request.POST

        if 'products' in request.POST:
            product_limits_calculation(post_data, Limits, Expense, ProductCount, request.user.id)
            return redirect('/expenses-chart/')
        else:
            adding_money(post_data, Expense, request.user.id)
        return redirect('/expenses-chart/')

    expenses: collections.Iterable = Expense.objects.all().filter(user_id=request.user.id).order_by('date')
    dates: list = [expense.date.strftime('%Y-%m-%d %H:%M:%S') for expense in expenses]
    amounts: list = [float(expense.amount) for expense in expenses]
    limits: collections.Iterable = Limits.objects.all().filter(user_id=request.user.id)
    total: dict = asyncio.run(convert_amount(amounts))
    chart: str = chart_calculation(dates, amounts)
    product_dict: dict = get_products_left(ProductCount, Limits, request.user.id)
    encoded_image: base64 = group_histogram(product_dict)
    return render(request, 'expenses_chart.html', {'chart': chart,
                                                   'total_money': total,
                                                   'limits': limits,
                                                   'product_data': product_dict,
                                                   'get_item': get_item,
                                                   'encoded_image': encoded_image})


def details(request):
    expenses = Expense.objects.all().filter(user_id=request.user.id)
    if request.method == 'POST':
        if 'Del' in request.POST:
            del_object = Expense.objects.filter(id=int(request.POST['id'])).all()
            del_object.delete()
            return redirect('/expenses-chart/details')

        elif 'time' in request.POST:
            selected_time = request.POST.get('time', None)
            range_expenses = time_range_expenses(selected_time, expenses, request.user.id)
            return render(request, 'details.html', {'expenses': range_expenses})

        return redirect(f'/expenses-chart/details/edit/id_data={int(request.POST["id"])}')
    return render(request, 'details.html', {'expenses': expenses})


def edit(request, id_data):
    data = Expense.objects.get(id=int(id_data))
    money = int(data.amount)
    cents = data.amount - int(money)
    date = data.date.strftime('%Y-%m-%d %H:%M:%S')
    if request.method == "POST":
        post_data = request.POST
        amount = money_amount_validation(post_data)
        data.amount = amount
        data.description = post_data['comment']
        data.date = post_data['date']
        data.save()

        return redirect('/expenses-chart/details/')

    return render(request, 'details_edit.html', {'data': data, 'money': money, 'cents': cents, 'date': date})


def add_limit(request):
    if request.method == 'POST':
        if request.POST['date'] == '':
            date = datetime.now().astimezone(tz=None)
        else:
            date = datetime.strptime(request.POST['date'], '%Y-%m-%d %H:%M:%S').astimezone(tz=None)
        if request.POST['time'] == 'month':
            end_limit_date = date.replace(
                month=date.month + 1)
        elif request.POST['time'] == 'year':
            end_limit_date = date.replace(
                year=date.year + 1)
        new_limit = Limits.objects.create(
            product_name=request.POST['product'],
            product_amount=request.POST['amount'],
            limit=int(request.POST['limit']),
            description=request.POST['description'],
            date=date,
            end_limit_date=end_limit_date,
            user_id=request.user.id
        )
        new_limit.save()
        new_product = ProductCount.objects.create(
            number_of_products=0,
            product_id_id=new_limit.id
        )
        new_product.save()
        return redirect('/expenses-chart/')

    return render(request, 'limit.html')


@csrf_exempt
def get_bot_info(request):
    bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)
    if request.method == 'POST':
        chat_id = request.POST['chat_id']
        data = TelegramChatID.objects.filter(chat_id=chat_id).first()
        if data:
            expenses_data = Expense.objects.filter(user_id=data.user_id).all()

        else:
            new_chat = TelegramChatID.objects.create(
                chat_id=chat_id,
                user_id=request.user.id
            )
            new_chat.save()
            expenses_data = Expense.objects.filter(user_id=new_chat.user_id).all()
        amounts: list = [float(expense.amount) for expense in expenses_data]
        bot.send_message(chat_id, f"Загальна Сумма: {sum(amounts)}")
        return JsonResponse({'status': 'success'})
    token = get_token(request)
    return JsonResponse({'csrftoken': token})
