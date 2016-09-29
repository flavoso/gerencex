from datetime import timedelta, datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, resolve_url as r
from django.utils import timezone
from django.views.generic import ListView
from gerencex.core.forms import AbsencesForm
from gerencex.core.models import Timing, Restday, Absences


@login_required
def home(request):
    return render(request, 'index.html')


@login_required
def timing_new(request):
    activate_timezone()

    if request.method == 'POST':
        if request.user.userdetail.atwork:
            request.user.userdetail.atwork = False
            request.user.userdetail.save()
            ticket = Timing(user=request.user, checkin=False, created_by=request.user)
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
            ticket = Timing.objects.create(user=request.user,
                                           checkin=True,
                                           created_by=request.user)

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


def forgotten_checkouts(request):
    """Get the check ins which have no check outs at the same day, via an indirect approach: two
    consecutive check ins indicate the target."""

    queryset = Timing.objects.all().order_by('user', 'date_time')
    tickets = [entry for entry in queryset]  # Caching the queryset, to avoid new database lookups

    regs = []

    lim = len(tickets) - 1
    for idx in range(0, lim):
        t1 = tickets[idx]
        t2 = tickets[idx + 1]
        if t1.user == t2.user and t1.checkin and t2.checkin:
            regs.append({
                'pk': t1.pk,
                'name': t1.user.first_name,
                'date': t1.date_time
            })

    return render(request, 'forgotten_checkouts.html', {'regs': regs})


def absence_new(request):

    if request.method == 'POST':
        form = AbsencesForm(request.POST)
        if form.is_valid():
            credit = form.cleaned_data['credit'].seconds
            debit = form.cleaned_data['debit'].seconds
            date = form.cleaned_data['begin']
            while date <= form.cleaned_data['end']:
                absence = Absences(date=date,
                                   user=form.cleaned_data['user'],
                                   cause=form.cleaned_data['cause'],
                                   credit=credit,
                                   debit=debit,
                                   )
                absence.save()
                date += timedelta(days=1)
            return HttpResponseRedirect(r('absences', username=form.cleaned_data['user'].username))
        else:
            return render(request, 'newabsence.html', {'form': form})
    else:
        form = AbsencesForm()
        return render(request, 'newabsence.html', {'form': form})


def absences(request, username):
    user = User.objects.get(username=username)
    data = []
    for d in Absences.objects.filter(user=user).all():
        data.append({'date': d.date,
                     'cause': d.get_cause_display(),
                     'credit': timedelta(seconds=d.credit),
                     'debit': timedelta(seconds=d.debit)})

    return render(request, 'absences.html', {'absences': data,
                                             'first_name': user.first_name,
                                             'last_name': user.last_name})


@login_required
def hours_bank(request):
    render(request, 'hours_bank.html')


@login_required
def my_hours_bank(request, username):
    render(request, 'my_hours_bank.html', {'username': username})


@login_required
def rules(request):
    render(request, 'rules.html')


def activate_timezone():
    timezone.activate(pytz.timezone('America/Sao_Paulo'))


def calculate_credit(user, date):
    """Crédito é calculado da seguinte forma: para cada dia, somam-se as parcelas compostas pela
       * soma das diferenças entre horas de saída e de entrada (tabela "Timing");
       * soma dos créditos eventualmente existentes na tabela "Absences"
    """
    tickets = [x for x in Timing.objects.filter(user=user, date_time__date=date).all()]
    if len(tickets) % 2 != 0:
        del tickets[-1]
