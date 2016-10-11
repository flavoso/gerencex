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
from gerencex.core import parameters


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
        context['time'] = ticket.date_time + parameters.CHECKIN_TOLERANCE
    else:
        context['register'] = 'saída'
        context['time'] = ticket.date_time + parameters.CHECKOUT_TOLERANCE
    return render(request, 'timing.html', context)


@login_required
def timing_fail(request):
    return render(request, 'timing_fail.html')


@login_required
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


@login_required
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


@login_required
def absences(request, username):
    user = get_object_or_404(User, username=username)
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
    return render(request, 'hours_bank.html')


@login_required
def my_hours_bank(request, username):
    user = User.objects.get(username=username)
    return render(request, 'my_hours_bank.html', {'first_name': user.first_name,
                                                  'last_name': user.last_name})


@login_required
def rules(request):
    return render(request, 'rules.html')


def activate_timezone():
    timezone.activate(pytz.timezone('America/Sao_Paulo'))


def calculate_credit(user, date):
    """
    Returns the credit for the pair user + date, as a timedelta

    Credit is calculated by summing up:
     * the credit from Timing table;
     * the credit from Absences table
    """

    tickets = [{'checkin': x.checkin, 'date_time': x.date_time}
               for x in Timing.objects.filter(user=user,
                                              date_time__date=date).all()
               ]

    # If the last Timing recorded is a checkin, it must not be considered in the credit calculus
    if tickets[-1]['checkin']:
        del tickets[-1]

    # Calculates the credit from the Timing table
    credit = timedelta(seconds=0)
    tolerance = parameters.CHECKOUT_TOLERANCE - parameters.CHECKIN_TOLERANCE

    if parameters.MAX_CHECKOUT_TIME['used'] or parameters.MIN_CHECKIN_TIME['used']:
        tickets = adjusted_tickets(tickets)

    if len(tickets) != 0:
        for ticket in tickets:
            if not ticket['checkin']:
                chkin = tickets.index(ticket) - 1
                credit += ticket['date_time'] - tickets[chkin]['date_time'] + tolerance

    # Sums up the credit from Absences table
    # There's only one user + date peer, due to the unique_together clause

    absences = [a for a in Absences.objects.filter(user=user, date=date)]
    credit_sum = timedelta(seconds=0)
    if absences:
        credit_int = absences[0].credit
        credit_sum = timedelta(seconds=credit_int)
    credit += credit_sum

    max_credit = parameters.MAX_DAILY_CREDIT

    if max_credit['used'] and credit > max_credit['value']:
        credit = max_credit['value']

    return credit


def calculate_debit(user, date):
    """
    Restday:        debit = restday.work_hours
    Absence day:    debit = REGULAR_WORK_HOURS + absence.debit
    Normal day:     debit = REGULAR_WORK_HOURS

    Debit is returned as a timedelta
    """
    restday = Restday.objects.filter(date=date)
    absence = Absences.objects.filter(user=user, date=date)

    # If date is a restday, let's consider the work hours specified for this date
    if restday.count():
        return restday[0].work_hours
    elif absence.count():
        return parameters.REGULAR_WORK_HOURS - timedelta(seconds=absence[0].debit)
    else:
        return parameters.REGULAR_WORK_HOURS


def adjusted_tickets(tickets):
    """
    Forces the checkin time to be greater than or equal to the minimum allowed.
    Forces the checkout time to be lesser than or equal to the maximum allowed.
    """
    utc_offset = datetime.now(pytz.timezone('America/Sao_Paulo')).utcoffset()
    # tz = pytz.timezone('America/Sao_Paulo')
    new_tickets = []

    for ticket in tickets:
        ticket['date_time'] = ticket['date_time'] + utc_offset
        # ticket['date_time'] = ticket['date_time'].astimezone(tz).replace(tzinfo=None)
        new_ticket = ticket

        if ticket['checkin'] and parameters.MIN_CHECKIN_TIME['used']:
            if ticket['date_time'].time() < parameters.MIN_CHECKIN_TIME['value']:
                hour = parameters.MIN_CHECKIN_TIME['value'].hour
                minute = parameters.MIN_CHECKIN_TIME['value'].minute
                new_ticket['date_time'] = ticket['date_time'].replace(
                    hour=hour, minute=minute)

        elif (not ticket['checkin']) and parameters.MAX_CHECKOUT_TIME['used']:
            if ticket['date_time'].time() > parameters.MAX_CHECKOUT_TIME['value']:
                hour = parameters.MAX_CHECKOUT_TIME['value'].hour
                minute = parameters.MAX_CHECKOUT_TIME['value'].minute
                new_ticket['date_time'] = ticket['date_time'].replace(
                    hour=hour, minute=minute)
        new_tickets.append(new_ticket)

    return new_tickets
