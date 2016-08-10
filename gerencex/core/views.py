from datetime import timedelta

import pytz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, resolve_url as r
from django.utils import timezone
from gerencex.core.models import Timing


@login_required
def home(request):
    return render(request, 'index.html')

@login_required
def timing_new(request):
    activate_timezone()

    if request.method == 'POST':
        if request.user.userdetail.atwork == True:
            request.user.userdetail.atwork = False
            request.user.userdetail.save()
            ticket = Timing(user=request.user, checkin=False)
            """
            Checkout time is recorded only if there is a checkin in the same day.
            """
            date = ticket.date_time.date()
            valid_checkout = bool(Timing.objects.filter(date_time__date=date, checkin=True))

            if valid_checkout:
                ticket.save()
            else:
                return HttpResponseRedirect(r('timing_fail'))

        else:
            request.user.userdetail.atwork = True
            request.user.userdetail.save()
            ticket = Timing.objects.create(user=request.user, checkin=True)

        return HttpResponseRedirect(r('timing', ticket.pk))
    return render(request, 'timing_new_not_post.html')

@login_required
def timing(request, pk):
    activate_timezone()
    context = {}
    ticket = get_object_or_404(Timing, pk=pk)

    if ticket.checkin:
        context['register'] = 'entrada'
        context['time'] = ticket.date_time + timedelta(minutes=-10)
    else:
        context['register'] = 'saída'
        context['time'] = ticket.date_time + timedelta(minutes = 5)
    return render(request, 'timing.html', context)

@login_required
def timing_fail(request):
    return render(request, 'timing_fail.html')

def newrestday(request):
    return render(request, 'newrestday.html')

def restday(request, date):
    return render(request, 'restday.html')

def bhauditor(request):
    return render(request, 'bhauditor.html')

def bhoras(request):
    return render(request, 'bhoras.html')

def activate_timezone():
    timezone.activate(pytz.timezone('America/Sao_Paulo'))