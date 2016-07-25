from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from gerencex.core.models import UserDetail


@login_required
def home(request):
    return render(request, 'index.html')

@login_required
def regtime(request):
    context = {}
    context['post'] = False
    if request.POST:
        if request.user.userdetail.atwork:
            request.user.userdetail.atwork = False
        else:
            request.user.userdetail.atwork = True
        request.user.userdetail.save()
        context['post'] = True
    return render(request, 'regtime.html', context)

def bhauditor(request):
    return render(request, 'bhauditor.html')

def bhoras(request):
    return render(request, 'bhoras.html')