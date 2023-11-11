from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('money_spending.urls')),
    path('user/', include('user.urls')),
]
