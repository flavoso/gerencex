from datetime import timedelta
import pytz

from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from gerencex.core.models import Timing


@login_required
def home(request):
    return render(request, 'index.html')

@login_required
def timing(request):
    activate_timezone()
    context = {}
    context['post'] = False
    if request.POST:
        if request.user.userdetail.atwork:
            time = Timing.objects.create(user=request.user, checkin=False)
            context['time'] = time.date_time + timedelta(minutes = 5)
            request.user.userdetail.atwork = False
            context['register'] = 'saída'
        else:
            time = Timing.objects.create(user=request.user, checkin=True)
            context['time'] = time.date_time + timedelta(minutes = -10)
            request.user.userdetail.atwork = True
            context['register'] = 'entrada'
        request.user.userdetail.save()
        context['post'] = True
    return render(request, 'timing.html', context)

def restday(request):
    return render(request, 'restday.html')

def bhauditor(request):
    return render(request, 'bhauditor.html')

def bhoras(request):
    return render(request, 'bhoras.html')

def activate_timezone():
    timezone.activate(pytz.timezone('America/Sao_Paulo'))