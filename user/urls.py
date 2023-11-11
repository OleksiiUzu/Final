from django.urls import path
from . import views

urlpatterns = [
    path('login', views.user_login, name='login'),
    path('logout', views.user_logout, name='logout'),
    path('register', views.register, name='register'),
    path('info', views.info, name='info'),
]