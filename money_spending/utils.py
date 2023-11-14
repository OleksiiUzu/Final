import asyncio
import aiohttp

import base64
from io import BytesIO

from typing import Union, Coroutine, Any, Callable

import datetime

from django.contrib.auth.models import User
from plotly.offline import plot
import plotly.graph_objs as go

import matplotlib.pyplot as plt
import numpy as np

from pymemcache.client.base import Client

client = Client(('localhost', 11211))


def cache(async_fun) -> Callable[[], Coroutine[Any, Any, dict]]:
    async def wrapper() -> dict:
        cache_keys = ['USD', 'EUR', 'PLN']
        cache_values = []
        for iso_literal_code in cache_keys:
            result_cache = client.get(str(iso_literal_code))
            cache_values.append(result_cache)
        if all(cache_data is None for cache_data in cache_values):
            result = await async_fun()
            for key, value in result.items():
                client.set(key, str(float(value)), expire=60*60*5)
            return result
        else:
            result_dict = {}
            for key, value in zip(cache_keys, cache_values):
                result_dict[key] = float(value)
            return result_dict
    return wrapper


async def find_currency(iso_code: int, currency_data: list) -> tuple:
    for item in currency_data:
        if item["r030"] == iso_code:
            return item['cc'], item["rate"]


@cache
async def get_currency() -> Union[dict, ConnectionError]:
    today: str = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d')
    api = f'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?date={today}&json'
    currency_dict = {}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api) as response:
                if response.status == 200:
                    currency_data = await response.json()
                    currency_list = await asyncio.gather(
                        find_currency(840, currency_data),
                        find_currency(978, currency_data),
                        find_currency(985, currency_data)
                    )
                    for item in currency_list:
                        currency_dict[item[0]] = item[1]

                    return currency_dict
    except aiohttp.ClientError as CE:
        return {'Client Error': CE}


async def currency_calculation(total_value: int, value: int) -> float:
    return round(float(total_value) / value, 2)


async def convert_amount(amount: list) -> dict:
    currency = await get_currency()
    currency_dict = {}
    total_value = sum(amount)

    coroutines = [currency_calculation(total_value, value) for item, value in currency.items()]
    converted_amount_list = await asyncio.gather(*coroutines)

    for literal_code, converted_amount in zip(currency.keys(), converted_amount_list):
        currency_dict[literal_code] = converted_amount
    currency_dict['UAH'] = float(total_value)
    return currency_dict


def money_amount_validation(data: dict) -> Union[int, float]:
    cents = data["cents"]
    if '.' in cents:
        cents = cents.replace('.', '')
    if cents != '' or not all(x == '0' for x in cents):
        amount: float = float(f'{data["money"]}.{cents}')
    else:
        amount: int = int(f'{data["money"]}')
    return amount


def chart_calculation(dates: list, amounts: list) -> str:
    trace = go.Scatter(x=dates, y=amounts, mode='text+lines+markers', name='Витрати')
    data = [trace]
    layout = go.Layout(title='Графік витрат', xaxis={'title': 'Дата'}, yaxis={'title': 'Сума'})
    chart = plot({'data': data, 'layout': layout}, output_type='div')
    return chart


def product_limits_calculation(post_data, limits_model, expense_model, products_model, user_data) -> None:
    limits_items_list = []
    list_of_products_id = post_data.getlist('products')

    for id_data in list_of_products_id:
        limits = limits_model.objects.all().filter(user_id=user_data).filter(id=int(id_data))
        limits_items_list.append(limits)
    all_objects = [obj for queryset in limits_items_list for obj in queryset]
    user = User.objects.filter(id=user_data).first()
    for item in all_objects:
        expense_model.objects.create(
            amount=item.product_amount,
            date=datetime.datetime.now(),
            description=item.description,
            user_id=user,
            product_id=item.id
        )
        product = products_model.objects.all().filter(product_id=item.id)
        if not product:
            counter = 1
            products_model.objects.create(
                product_id=item,
                number_of_products=counter
            )
        else:
            counter = product[0].number_of_products + 1
            product[0].number_of_products = counter
            product[0].save()


def get_products_left(products_model, limit_model, user_data) -> dict:
    product_data = products_model.objects.select_related('product_id').all().filter(product_id__user=user_data).all()
    product_dict = {}
    for product in product_data:
        remainder = int(
            (int(product.product_id.limit) / int(product.product_id.product_amount)) - int(product.number_of_products)
                            )
        total_amount_of_product = int(int(product.product_id.limit) / int(product.product_id.product_amount))
        if remainder == 0 or product.product_id.end_limit_date == datetime.datetime.now():
            limit_model.objects.filter(id=product.product_id.id).delete()
            print('you have reached the limit')
        product_dict[product.product_id.product_name] = [remainder,
                                                         total_amount_of_product,
                                                         product.product_id.product_amount,
                                                         product.product_id.limit]
    return product_dict


def adding_money(post_data, expense_model, user_data) -> None:
    amount = money_amount_validation(post_data)
    user = User.objects.filter(id=user_data).first()
    if post_data['date'] == '':
        date = datetime.datetime.now()
    else:
        date_time = datetime.datetime.now()
        date = datetime.datetime.strptime(post_data['date'], '%Y-%m-%d')
        date = date.replace(hour=int(date_time.hour),minute=int(date_time.minute),second=int(date_time.second))
    expense_model.objects.create(amount=amount,date=date,description=post_data['comment'],user_id=user)


def group_histogram(product_dict) -> base64:
    data = {}
    for key, value in product_dict.items():
        data[key] = [value[1], value[0]]
    fig, ax = plt.subplots()
    bar_width = 0.2
    index = np.arange(len(data))
    colors = ['g', 'r']

    for i, (label, values) in enumerate(data.items()):
        adjusted_index = i

        for j, value in enumerate(values):
            color_index = 1 if j == np.argmax(values) else 0
            ax.bar(adjusted_index, value, bar_width, label=f'{label} {j + 1}', color=colors[color_index])

    ax.set_xlabel('Продукти')
    ax.set_ylabel('Кількість')
    ax.set_title('Хістограма Лімітів')
    ax.set_xticks(index)
    ax.set_xticklabels(data.keys())

    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    encoded_image = base64.b64encode(image_stream.read()).decode('utf-8')

    return encoded_image


def time_range_expenses(time, expense_object, user) -> object:
    expenses = expense_object.filter(user_id=user)
    if time == 'month':
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        expenses = expense_object.filter(date__month=month).filter(date__year=year)
    elif time == 'year':
        year = datetime.datetime.now().year
        expenses = expense_object.filter(date__year=year)
    elif time == 'all':
        expenses = expense_object.filter(user_id=user)
    return expenses
