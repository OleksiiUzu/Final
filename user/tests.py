from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client


class UserTest(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='alex',
            password='123'
        )
        self.user_client = Client()
        self.user_client.login(username='alex', password='123')
        self.register_info = {'username': 'somName',
                              'firstname': 'firstname',
                              'lastname': 'lastname',
                              'password': 'somePassword',
                              'email': 'someEmail@example.com'}

    def test_user_login(self):
        response = self.user_client.post('/user/login', {'username': 'alex', 'password': '123'})
        status_code = response.status_code
        self.assertEqual(status_code, 302)

    def test_user_register(self):
        self.user_client.logout()
        response = self.user_client.post('/user/register', self.register_info)
        response_get = self.user_client.get('/user/register')
        self.assertEqual(response_get.status_code, 200)
        status_code = response.status_code
        self.assertEqual(status_code, 302)

        created_user = User.objects.filter(username='somName').first()
        self.assertIsNotNone(created_user)

        login_response = self.user_client.login(username='somName', password='somePassword')
        self.assertTrue(login_response)
        self.assertTrue('Location' in response)
        self.assertIn('/user/login', response['Location'])

    def test_user_logout(self):
        response = self.user_client.get('/user/logout')
        self.assertEqual(response.status_code, 302)

    def test_user_info(self):
        response = self.user_client.get('/user/info')
        self.assertEqual(response.status_code, 200)

    def test_main(self):
        response = self.user_client.get('/')
        self.assertEqual(response.status_code, 200)

        self.user_client.logout()

        response = self.user_client.get('/')
        self.assertEqual(response.status_code, 302)
