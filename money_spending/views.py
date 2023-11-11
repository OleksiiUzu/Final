import asyncio
from datetime import datetime

from django.shortcuts import render, redirect

from .templatetags.filters import get_item
from .models import Expense, Limits, ProductCount
from .utils import (money_amount_validation,
                    convert_amount,
                    chart_calculation,
                    product_limits_calculation,
                    adding_money, get_products_left, group_histogram)


# add rise or sand message
# add choose from date to date
# add telegram bot


def index(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')
    return render(request, 'index.html')


def expenses_chart(request):
    if request.method == "POST":
        post_data = request.POST

        if 'products' in request.POST:
            product_limits_calculation(post_data, Limits, Expense, ProductCount, request.user)
        else:
            adding_money(post_data, Expense, request.user)
        return redirect('/expenses-chart/')

    expenses = Expense.objects.all().filter(user=request.user.id).order_by('date')
    print(expenses)
    dates = [expense.date.strftime('%Y-%m-%d %H:%M:%S') for expense in expenses]  # here can add timerange
    print(dates)
    amounts = [float(expense.amount) for expense in expenses]
    limits = Limits.objects.all().filter(user=request.user.id)
    total = asyncio.run(convert_amount(amounts))
    chart = chart_calculation(dates, amounts)
    product_dict = get_products_left(ProductCount, Limits, request.user.id)
    encoded_image = group_histogram(product_dict)
    return render(request, 'expenses_chart.html', {'chart': chart,
                                                   'total_money': total,
                                                   'limits': limits,
                                                   'product_data': product_dict,
                                                   'get_item': get_item,
                                                   'encoded_image': encoded_image})


def details(request):
    if request.method == 'POST':
        if 'Del' in request.POST:
            del_object = Expense.objects.filter(id=int(request.POST['id'])).all()
            del_object.delete()
            return redirect('/expenses-chart/details')
        if 'time' in request.POST:
            print(request.POST)
            for item in request.POST['time']:
                date = 0
                match item:
                    case 'day':
                        date = 1
                    case 'month':
                        date = 2
                    case 'year':
                        date = 3

                print(date)

            expenses = Expense.objects.all().filter(user=request.user.id).filter()
            return render(request, 'details.html', {'expenses': expenses})
        return redirect(f'/expenses-chart/details/edit/id_data={int(request.POST["id"])}')
    expenses = Expense.objects.all().filter(user=request.user.id)
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
        return redirect('/expenses-chart/limit/')

    return render(request, 'limit.html')
