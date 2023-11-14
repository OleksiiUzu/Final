from django.urls import path
from money_spending import views


urlpatterns = [
    path('', views.index, name='main'),
    path('expenses-chart/', views.expenses_chart, name='expenses_chart'),
    path('expenses-chart/limit/', views.add_limit, name='add_limit'),
    path('expenses-chart/details/', views.details, name='details'),
    path('expenses-chart/details/edit/id_data=<id_data>', views.edit, name='edit'),
    path('get_bot_info/', views.get_bot_info, name='get_bot_info'),
]
