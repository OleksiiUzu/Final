from django.contrib.auth import authenticate, logout, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from user.models import User


def user_login(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            response_text = 'fail'
            status_code = 404
            return HttpResponse(response_text, status=status_code)
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'login.html', {})


def user_logout(request):
    logout(request)
    return redirect('/user/login')


def register(request):
    if request.method == 'POST':
        new_user = User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password'],
            email=request.POST['email'],
            first_name=request.POST['firstname'],
            last_name=request.POST['lastname']
            )
        new_user.save()
        return redirect('/user/login')
    return render(request, 'register.html', {})


def info(request):
    user = User.objects.get(id=request.user.id)
    return render(request, 'user_info.html', {'user': user})
