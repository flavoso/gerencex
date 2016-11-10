import socket
from datetime import timedelta, datetime, date

import pytz
from decouple import config
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, resolve_url as r
from django.utils import timezone
from gerencex.core.forms import AbsencesForm, GenerateBalanceForm
from gerencex.core.models import Timing, Absences, Restday, HoursBalance, Office
from gerencex.core.time_calculations import calculate_credit, calculate_debit


@login_required
def home(request):
    at_work = request.user.userdetail.atwork
    status = 'entrada' if at_work else 'saída'
    tickets = Timing.objects.filter(user=request.user)
    date_time = tickets.last().date_time if tickets else ''
    lines = HoursBalance.objects.filter(user=request.user)
    balance = lines.last().time_balance() if lines else ''
    context = {
        'status': status,
        'date_time': date_time,
        'balance': balance
    }
    return render(request, 'index.html', context)


@login_required
def timing_new(request):
    activate_timezone()

    # The check ins and checkouts are allowed only at office. We try to guarantee this by
    # assuring that the client IP is close to the company IP. Do you suggest a best test?

    company_site = config('COMPANY_SITE', default='')
    company_ips = socket.gethostbyname_ex(company_site)[2] if company_site else ''
    client_ip = get_client_ip(request)[1]
    client_local_ip = get_client_ip(request)[0]
    client_partial_ip = ".".join(client_ip.split('.')[0:3])

    # We need to allow check ins and checkouts from developer workstation, to avoid breaking the
    # tests
    server_hostname = socket.gethostname()
    valid_hostname = config('DEVELOPER_HOSTNAME', default='')

    if not (server_hostname == valid_hostname or client_partial_ip in " ".join(company_ips)):
        return render(request, 'invalid_check.html')

    if request.method == 'POST':
        if request.user.userdetail.atwork:
            request.user.userdetail.atwork = False
            request.user.userdetail.save()
            ticket = Timing(user=request.user,
                            checkin=False,
                            created_by=request.user,
                            client_ip=client_ip,
                            client_local_ip=client_local_ip)
            """
            Checkout time is recorded only if there is a checkin in the same day.
            """
            utc_offset = datetime.now(pytz.timezone('America/Sao_Paulo')).utcoffset()
            date_ = (ticket.date_time + utc_offset).date()
            valid_checkout = bool(Timing.objects.filter(date_time__date=date_, checkin=True))

            if valid_checkout:
                ticket.save()
            else:
                return HttpResponseRedirect(r('timing_fail'))
        else:
            request.user.userdetail.atwork = True
            request.user.userdetail.save()
            ticket = Timing.objects.create(user=request.user,
                                           checkin=True,
                                           created_by=request.user,
                                           client_ip=client_ip,
                                           client_local_ip=client_local_ip)
        return HttpResponseRedirect(r('timing', ticket.pk))
    return render(request, 'timing_new_not_post.html')


@login_required
def timing(request, pk):
    activate_timezone()
    context = {}
    ticket = get_object_or_404(Timing, pk=pk)

    if ticket.checkin:
        context['register'] = 'entrada'
        context['time'] = ticket.date_time
    else:
        context['register'] = 'saída'
        context['time'] = ticket.date_time
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
            credit = form.cleaned_data['credit'].total_seconds()
            debit = form.cleaned_data['debit'].total_seconds()
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
    """
    Shows the balance of hours of office workers
    """
    office = request.user.userdetail.office
    users = [u.user for u in office.users.all()]
    date_ = timezone.now().date()
    expected_balance_date = date_ - timedelta(days=1)

    # Updates HoursBalance, if needed
    if office.last_balance_date < expected_balance_date:
        for d in dates(office.last_balance_date, date_):
            for user in users:
                UserBalance(user, year=d.year, month=d.month).create_or_update_line(d)
        office.last_balance_date = date_
        office.save()
    lines = []

    for user in users:
        lines.append(
            {'username': user.username,
             'first_name': user.first_name,
             'last_name': user.last_name,
             'balance': HoursBalance.objects.filter(
                 user=user,
                 date=expected_balance_date).first().time_balance()
             }
        )
    return render(request, 'hours_bank.html',
                  {'office': office,
                   'lines': lines}
                  )


@login_required
def my_hours_bank(request, username, year, month):
    user = User.objects.get(username=username)
    start_control_date = user.userdetail.office.hours_control_start_date
    min_valid_date = date(start_control_date.year, start_control_date.month, 1)
    balance_date = date(int(year), int(month), 1)

    if balance_date < min_valid_date:
        return render(request,
                      'nonexistent_balance.html',
                      {'min_valid_year': str(min_valid_date.year),
                       'min_valid_month': str(min_valid_date.month),
                       'min_valid_date': min_valid_date,
                       'first_name': user.first_name,
                       'last_name': user.last_name,
                       'username': username}
                      )

    try_previous = balance_date - timedelta(days=1)
    try_next = balance_date + timedelta(days=31)
    previous_exists = HoursBalance.objects.filter(date__year=try_previous.year,
                                                  date__month=try_previous.month,
                                                  user=user)

    next_exists = HoursBalance.objects.filter(date__year=try_next.year,
                                              date__month=try_next.month,
                                              user=user)

    previous = None
    next_ = None

    if previous_exists:
        previous = {'year': str(try_previous.year), 'month': str(try_previous.month)}

    if next_exists:
        next_ = {'year': str(try_next.year), 'month': str(try_next.month)}

    lines = UserBalance(user, year=year, month=month).get_monthly_lines()

    return render(request, 'my_hours_bank.html', {'lines': lines,
                                                  'username': username,
                                                  'first_name': user.first_name,
                                                  'last_name': user.last_name,
                                                  'date': balance_date,
                                                  'previous': previous,
                                                  'next': next_})


@login_required
def calculate_hours_bank(request):
    """
    (Re)Generates the hours balance for all users in the office
    """
    if request.method == 'POST':
        form = GenerateBalanceForm(request.POST)
        if form.is_valid():
            office = request.user.userdetail.office
            start_control = office.hours_control_start_date
            form_begin = form.cleaned_data['begin']
            users = [x.user for x in office.users.all()]
            begin_date = start_control if not form_begin else form_begin
            end_date = timezone.now().date()

            for date_ in dates(begin_date, end_date):
                for user in users:
                    updated_values = {
                        'credit': calculate_credit(user, date_).total_seconds(),
                        'debit': calculate_debit(user, date_).total_seconds()
                    }
                    HoursBalance.objects.update_or_create(
                        date=date_,
                        user=user,
                        defaults=updated_values
                    )
            office.last_balance_date = end_date
            office.save()
            return HttpResponseRedirect(r('hours_bank'))
        else:
            return render(request, 'calculate_bank.html', {'form': form})
    else:
        form = GenerateBalanceForm()
        return render(request, 'calculate_bank.html', {'form': form})


@login_required
def rules(request):
    office = request.user.userdetail.office
    params = []
    params.append({
        'description': Office._meta.get_field('regular_work_hours').verbose_name,
        'active': True,
        'value': str(office.regular_work_hours)
        }
    )
    params.append({
        'description': Office._meta.get_field('min_work_hours_for_credit').verbose_name,
        'active': office.min_work_hours_for_credit,
        'value': str(office.min_work_hours_for_credit_value)
        }
    )
    params.append({
        'description': Office._meta.get_field('max_daily_credit').verbose_name,
        'active': office.max_daily_credit,
        'value': office.max_daily_credit_value
        }
    )
    params.append({
        'description': Office._meta.get_field('max_monthly_balance').verbose_name,
        'active': office.max_monthly_balance,
        'value': office.max_monthly_balance_value
        }
    )
    params.append({
        'description': Office._meta.get_field('min_checkin_time').verbose_name,
        'active': office.min_checkin_time,
        'value': office.min_checkin_time_value
        }
    )
    params.append({
        'description': Office._meta.get_field('max_checkout_time').verbose_name,
        'active': office.max_checkout_time,
        'value': office.max_checkout_time_value
        }
    )
    params.append({
        'description': Office._meta.get_field('checkin_tolerance').verbose_name,
        'active': True,
        'value': office.checkin_tolerance
        }
    )
    params.append({
        'description': Office._meta.get_field('checkout_tolerance').verbose_name,
        'active': True,
        'value': office.checkout_tolerance
        }
    )

    return render(request, 'rules.html', {'params': params})


def activate_timezone():
    timezone.activate(pytz.timezone('America/Sao_Paulo'))


def dates(date1, date2):
    d = date1
    while d < date2:
        yield d
        d += timedelta(days=1)


def comments(user, date_):
    restday = Restday.objects.filter(date=date_).last()
    absence = Absences.objects.filter(date=date_, user=user).last()
    office = user.userdetail.office
    start_balance = bool(date_ == office.hours_control_start_date)
    weekend = bool(date_.weekday() in (5, 6))

    msg = ''
    if weekend:
        msg += 'Fim de semana. '

    if restday:
        msg += restday.note + '. '

    if absence:
        msg += absence.get_cause_display() + '. '

    if start_balance:
        msg += 'Abertura da conta de horas. '

    return msg


class UserBalance:
    def __init__(self, user, **kwargs):
        self.user = user
        self.office = user.userdetail.office
        self.year = int(kwargs['year'])
        self.month = int(kwargs['month'])
        self.last_month_day = date(self.year, self.month + 1, 1)
        self.last_day = min(timezone.now().date(), self.last_month_day)
        self.start_date = user.userdetail.office.hours_control_start_date
        first_month_day = date(self.year, self.month, 1)
        self.first_day = max(first_month_day, self.start_date)
        balance = [l for l in HoursBalance.objects.filter(date__year=self.year,
                                                          date__month=self.month,
                                                          user=self.user)]
        self.balance_dates = [d.date for d in balance]

    def get_monthly_lines(self):
        lines = []
        for date_ in dates(self.first_day, self.last_day):
            if date_ not in self.balance_dates:
                HoursBalance.objects.create(
                    date=date_,
                    user=self.user,
                    credit=calculate_credit(self.user, date_).total_seconds(),
                    debit=calculate_debit(self.user, date_).total_seconds()
                )

            line = HoursBalance.objects.get(user=self.user, date=date_)

            lines.append({'date': date_,
                          'credit': line.time_credit(),
                          'debit': line.time_debit(),
                          'balance': line.time_balance(),
                          'comment': comments(self.user, date_)})
        self.update_last_balance_date(self.last_day)
        return lines

    def create_or_update_line(self, date_):
        credit = calculate_credit(self.user, date_).total_seconds()
        debit = calculate_debit(self.user, date_).total_seconds()
        updated_values = {'credit': credit, 'debit': debit}
        HoursBalance.objects.update_or_create(
            date=date_,
            user=self.user,
            defaults=updated_values
        )

    def update_last_balance_date(self, date_):
        self.office.last_balance_date = date_
        self.office.save()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ips = []
    if x_forwarded_for:
        ips.append(x_forwarded_for.split(',')[0])
        ips.append(x_forwarded_for.split(',')[-1])
    else:
        ips.append('')
        ips.append(request.META.get('REMOTE_ADDR'))
    return ips
