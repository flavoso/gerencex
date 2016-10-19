from datetime import timedelta, datetime, date

import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, resolve_url as r
from django.utils import timezone
from gerencex.core.forms import AbsencesForm
from gerencex.core.models import Timing, Absences, Restday, HoursBalance
from gerencex.core.time_calculations import calculate_credit, calculate_debit


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
        checkin_tolerance = request.user.userdetail.office.checkin_tolerance
        context['register'] = 'entrada'
        context['time'] = ticket.date_time - checkin_tolerance
    else:
        checkout_tolerance = request.user.userdetail.office.checkout_tolerance
        context['register'] = 'saída'
        context['time'] = ticket.date_time + checkout_tolerance
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
def my_hours_bank(request, username, year, month):
    user = User.objects.get(username=username)
    office = user.userdetail.office
    # initial_data = office.
    return render(request, 'my_hours_bank.html', {'first_name': user.first_name,
                                                  'last_name': user.last_name})


@login_required
def rules(request):
    return render(request, 'rules.html')


def activate_timezone():
    timezone.activate(pytz.timezone('America/Sao_Paulo'))


class Balance:
    def __init__(self, user, year, month):
        self.user = user
        self.year = int(year)
        self.month = int(month)

    def first_day(self):
        office = self.user.userdetail.office
        start_date = office.hours_control_start_date

        if start_date < date(self.year, self.month, 1):
            return {'date': date(self.year, self.month, 1),
                    'first_balance': False}
        else:
            return {'date': start_date,
                    'first_balance': True}

    def last_work_day(self):
        last_month_day = date(self.year, self.month + 1, 1) - timedelta(days=1)
        last_work_day = last_month_day
        weekend = (5, 6)
        restdays = [d.date for d in Restday.objects.filter(date__year = 2016, date__month = 10)]
        while last_work_day.weekday() in weekend or last_work_day.weekday() in restdays:
            last_work_day -= timedelta(days=1)
        return last_work_day

    def lines(self):
        last_month_day = date(self.year, self.month + 1, 1) - timedelta(days=1)
        dates = [self.first_day()[date]]
        d = self.first_day()[date]
        while d.day < last_month_day.day:
            d += timedelta(days=1)
            dates.append(d)

        balance = [l for l in HoursBalance.objects.filter(date__year=self.year,
                                                        date__month=self.month,
                                                        user=self.user)]
        balance_dates = [d.date for d in balance]
        lines = []
        for date_ in dates:
            if date_ in balance_dates:
                idx = balance_dates.index(date_)
                credit = balance[idx].credit
                debit = balance[idx].debit
                balance = balance[idx].debit
            else:
                credit = calculate_credit(self.user, date_).seconds
                debit = calculate_debit(self.user, date_).seconds
                HoursBalance.objects.create(date=date_,
                                            user=self.user,
                                            credit=credit,
                                            debit=debit)
                balance = HoursBalance.objects.filter(user=self.user, date=date_)[0].balance

            lines.append({'date': date_,
                          'credit': credit,
                          'debit': debit,
                          'balance': balance,
                          'comment': ''})
        return lines