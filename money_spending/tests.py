import asyncio
from _decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase, Client
import datetime

from money_spending.models import Expense, Limits, ProductCount
from money_spending.utils import (money_amount_validation,
                                  convert_amount,
                                  chart_calculation,
                                  product_limits_calculation,
                                  adding_money,
                                  get_products_left,
                                  group_histogram,
                                  time_range_expenses,
                                  get_currency,
                                  find_currency)

from unittest.mock import patch, Mock


class TestUtils(TestCase):
    def setUp(self) -> None:
        fixtures = ['money_spending.json']

        self.user_client = Client()
        self.user_data = {'username': 'test', 'password': 'test', 'id': 2}
        self.post_data_float = {'money': '12', 'cents': '11', 'date': '2023-11-09', 'comment': ''}
        self.post_data_int = {'money': '12', 'cents': '', 'date': '', 'comment': '238'}
        self.post_data_dot = {'money': '12', 'cents': '1.1', 'date': '', 'comment': '238'}
        self.user_instance = User.objects.create(**self.user_data)
        self.user_client.force_login(self.user_instance)
        self.expenses = Expense.objects.filter(user_id=int(self.user_instance.id))
        self.limits = Limits.objects.filter(user_id=int(self.user_instance.id))
        self.product_count = ProductCount.objects.all()
        self.amounts: list = [float(expense.amount) for expense in self.expenses]
        self.dates: list = [expense.date.strftime('%Y-%m-%d %H:%M:%S') for expense in self.expenses]
        self.currency_data = [
            {"r030": 840, 'cc': 'USD', 'rate': 123.1},
            {"r030": 978, 'cc': 'EUR', 'rate': 118.1},
            {"r030": 985, 'cc': 'USD', 'rate': 124.1},
            {"r030": 123, 'cc': 'ZZA', 'rate': 0.1}]
        self.limit_product = Limits.objects.create(
            product_name='Cofee',
            product_amount=40,
            limit=500,
            date=datetime.datetime.now(),
            end_limit_date=datetime.datetime.now() + datetime.timedelta(days=30),
            user_id=self.user_instance.id)

    def test_adding_money(self):
        self.user_client.login(username='alex', password='123')
        self.data1 = {'money': '12', 'cents': '11', 'date': '2023-11-09', 'comment': ''}
        self.data2 = {'money': '12', 'cents': '11', 'date': '', 'comment': '234'}
        self.data3 = {'money': '12', 'cents': '', 'date': '', 'comment': '238'}
        adding_money(self.data1, Expense, self.user_instance.id)
        adding_money(self.data2, Expense, self.user_instance.id)
        adding_money(self.data3, Expense, self.user_instance.id)

        expense1 = Expense.objects.get(description='')
        expense2 = Expense.objects.get(description='234')

        self.assertEqual(
            expense1.date.strftime('%Y-%m-%d'),
            str(datetime.datetime.strptime('2023-11-09', '%Y-%m-%d').date()))
        self.assertEqual(expense1.description, '')
        self.assertEqual(expense2.amount, Decimal('12.11'))

    def test_money_amount_validation(self):
        result = money_amount_validation(self.post_data_float)
        self.assertIsInstance(result, float)
        result = money_amount_validation(self.post_data_int)
        self.assertIsInstance(result, int)
        result = money_amount_validation(self.post_data_dot)
        self.assertIsInstance(result, float)

    def test_convert_amount(self):
        self.client.login(username='alex', password='123')
        asyncio.run(convert_amount(self.amounts))

    def test_chart_calculation(self):
        chart_calculation(self.dates, self.amounts)

    def test_find_currency(self):
        result = asyncio.run(find_currency(840, self.currency_data))
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ('USD', 123.1))

    @patch('money_spending.views.product_limits_calculation')
    @patch('money_spending.views.get_products_left')
    def test_expense_chart(self, mock_get_products_left, mock_product_limits_calculation):
        response = self.user_client.get('/expenses-chart/')
        self.assertEqual(response.status_code, 200)

        post_data_product = {'products': ['1', '2']}
        response_post_product = self.user_client.post('/expenses-chart/', post_data_product)
        self.assertEqual(response_post_product.status_code, 302)

        post_data_money = {'money': '12', 'cents': '', 'date': '', 'comment': ''}
        response_post_money = self.user_client.post('/expenses-chart/', post_data_money)
        self.assertEqual(response_post_money.status_code, 302)

        mock_get_products_left.return_value = ProductCount

        mock_get_products_left.assert_called_with(ProductCount, Limits, self.user_instance.id)
        mock_product_limits_calculation.assert_called_with(post_data_product, Limits, Expense, ProductCount, self.user_instance.id)

    def test_details(self):

        response = self.user_client.get('/expenses-chart/details/')
        self.assertEqual(response.status_code, 200)
        del_data = {'Del': 'Видалити', 'id': '1'}
        post_response = self.user_client.post('/expenses-chart/details/', del_data)
        self.assertEqual(post_response.status_code, 302)
        time_data_current_month = {'time': 'month'}
        time_data_current_year = {'time': 'year'}
        time_data_current_all = {'time': 'all'}
        post_response_month = self.user_client.post('/expenses-chart/details/', time_data_current_month)
        post_response_year = self.user_client.post('/expenses-chart/details/', time_data_current_year)
        post_response_all = self.user_client.post('/expenses-chart/details/', time_data_current_all)
        expenses = Expense.objects.all().filter(user_id=self.user_instance.id)
        result_month = time_range_expenses(time_data_current_month, expenses, self.user_instance.id)
        result_year = time_range_expenses(time_data_current_month, expenses, self.user_instance.id)
        result_all = time_range_expenses(time_data_current_month, expenses, self.user_instance.id)

        self.assertEqual(post_response_month.status_code, 200)
        self.assertEqual(post_response_year.status_code, 200)
        self.assertEqual(post_response_all.status_code, 200)
        self.assertQuerysetEqual(result_month, expenses)
        self.assertQuerysetEqual(result_year, expenses)
        self.assertQuerysetEqual(result_all, expenses)

    def test_get_currency(self):
        result = asyncio.run(get_currency())
        self.assertIsInstance(result, dict)

    def test_get_product_left_(self):
        another_post_data_product=ProductCount.objects.create(
            number_of_products=0,
            product_id=self.limit_product
        )
        post_data_product = ProductCount.objects.create(
            number_of_products=3,
            product_id=self.limit_product
        )
        post_data_product.save()
        another_post_data_product.save()
        result = get_products_left(ProductCount, Limits, self.user_instance.id)
        self.assertIsInstance(result, dict)

    def test_product_limits_calculation(self):
        post_data_product = {'products': ['1', '2']}
        test_post_data = Mock()
        test_post_data.getlist.return_value = ['1', '2', '3']
        response_post_product = self.user_client.post('/expenses-chart/', post_data_product)
        self.assertEqual(response_post_product.status_code, 302)

        product_limits_calculation(test_post_data, Limits, Expense, ProductCount, self.user_instance.id)

    def test_edit(self):
        expenses_data = Expense.objects.create(
            date=datetime.datetime.now(),
            amount=220,
            description='',
            user_id=self.user_instance
        )
        expenses_data.save()
        updated_data = {
            'date': '2023-11-14',
            'money': 300,
            'cents': 3,
            'comment': 'Updated description',
            'user_id': self.user_instance.id
        }
        response = self.user_client.post(f'/expenses-chart/details/edit/id_data={expenses_data.id}', updated_data)
        response_get = self.user_client.get(f'/expenses-chart/details/edit/id_data={expenses_data.id}')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response_get.status_code, 200)

    def test_index(self):
        response = self.user_client.get('/')
        self.assertEqual(response.status_code, 200)
        self.user_client.logout()
        response = self.user_client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_add_limit(self):
        response = self.user_client.get('/expenses-chart/limit/')
        self.assertEqual(response.status_code, 200)
        post_data = {'date': str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), 'time': 'month',
                     'product': 'Cofee', 'amount': 40, 'limit': 300, 'description': ''}
        response = self.user_client.post('/expenses-chart/limit/', post_data)
        post_data_2 = {'date': str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), 'time': 'year',
                     'product': 'Cofee', 'amount': 40, 'limit': 300, 'description': ''}
        response_2 = self.user_client.post('/expenses-chart/limit/', post_data_2)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response_2.status_code, 302)

        response = self.user_client.get('/expenses-chart/limit/')
        self.assertEqual(response.status_code, 200)

    def test_histogram(self):
        another_post_data_product = ProductCount.objects.create(
            number_of_products=0,
            product_id=self.limit_product
        )
        post_data_product = ProductCount.objects.create(
            number_of_products=3,
            product_id=self.limit_product
        )
        post_data_product.save()
        another_post_data_product.save()
        product_dict = get_products_left(ProductCount, Limits, self.user_instance.id)
        result = group_histogram(product_dict)
        self.assertIsInstance(result, str)
