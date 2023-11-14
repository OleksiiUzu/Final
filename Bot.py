from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
import asyncio
import requests
from t_token import telegram_token



bot = AsyncTeleBot(telegram_token)
django_app_url = 'http://localhost:8000/get_bot_info/'
client = requests.session()
client.get(django_app_url)


@bot.message_handler(commands=['total'])
async def send_total(message):
    # response_csrf = requests.get(django_app_url)
    # csrftoken = client.cookies.get('csrftoken', None)
    
    data = {
        'total': 'total',
        'chat_id': message.chat.id
    }
    requests.post('http://localhost:8000/get_bot_info/', data=data)


asyncio.run(bot.polling())
