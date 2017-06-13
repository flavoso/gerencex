import calendar
import socket
from datetime import timedelta, datetime, date

import pytz
from decouple import config
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, resolve_url as r
from django.utils import timezone
from gerencex.core.forms import AbsencesForm, GenerateBalanceForm
from gerencex.core.functions import get_client_ip, previous_next, \
    UserBalance, updates_hours_balance
from gerencex.core.models import Timing, Absences, Restday, HoursBalance, Office
from gerencex.core.time_calculations import DateData

current_tz = timezone.get_current_timezone()


@login_required
def home(request):
    today = timezone.now().date()
    balance_date = today - timedelta(days=1)
    at_work = request.user.userdetail.atwork

    def friendly(x):
        return 'entrada' if x else 'saída'

    status = friendly(at_work)
    tickets = Timing.objects.filter(user=request.user)
    date_time = tickets.last().date_time if tickets else ''
    line = HoursBalance.objects.filter(user=request.user, date=balance_date)
    balance = line.last().time_balance() if line else ''

    today_tickets = Timing.objects.filter(user=request.user, date_time__date=today).all()
    tickets = []
    if today_tickets:
        tickets = [
            {'status': friendly(x.checkin),
             'date_time': x.date_time}
            for x in today_tickets
        ]

    context = {
        'status': status,
        'date_time': date_time,
        'balance': balance,
        'tickets': tickets
    }
    return render(request, 'index.html', context)


@login_required
def timing_new(request):

    # The check ins and checkouts are allowed only at office. We try to guarantee this by
    # assuring that the client IP is close to the company IP. Do you suggest a better test?

    company_site = config('COMPANY_SITE', default='')
    company_ips = socket.gethostbyname_ex(company_site)[2] if company_site else ''
    client_ip = get_client_ip(request)[1]
    client_local_ip = get_client_ip(request)[0]
    client_partial_ip = ".".join(client_ip.split('.')[0:3])

    # We need to allow check ins and checkouts from developer workstation, to avoid breaking the
    # tests
    server_hostname = socket.gethostname()
    valid_hostname = config('DEVELOPER_HOSTNAME', default='')

#    if not (server_hostname == valid_hostname or client_partial_ip in " ".join(company_ips)):
#        return render(request, 'invalid_check.html')

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
            # utc_offset = datetime.now(pytz.timezone('America/Sao_Paulo')).utcoffset()
            # date_ = (ticket.date_time + utc_offset).date()
            date_ = ticket.date_time.astimezone(current_tz).date()
            required_checkin = timezone.make_aware(
                datetime(date_.year, date_.month, date_.day, 0, 0, 0),
            )
            valid_checkout = bool(Timing.objects.filter(user=request.user,
                                                        date_time__gte=required_checkin,
                                                        checkin=True))

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
def office_tickets(request):
    user = request.user
    office = user.userdetail.office
    users = [u.user for u in office.users.all()]
    context = {
        'office': office,
        'user': user,
        'users': users
    }
    return render(request, 'office_tickets.html', context)


@login_required
def forgotten_checkouts(request):
    """Get the check ins which have no check outs at the same day, via an indirect approach: two
    consecutive check ins indicate the target."""

    tickets = [x for x in Timing.objects.all().order_by('user', 'date_time')]

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
@permission_required('core.add_absences')
def absence_new(request):
    office = request.user.userdetail.office
    users = User.objects.filter(userdetail__office=office)
    if request.method == 'POST':
        form = AbsencesForm(request.POST, users=users)
        if form.is_valid():
            date_ = form.cleaned_data['begin']
            begin_ = form.cleaned_data['begin']
            end_ = form.cleaned_data['end']
            user = form.cleaned_data['user']
            cause = form.cleaned_data['cause']
            credit = form.cleaned_data['credit'].total_seconds()
            debit = form.cleaned_data['debit'].total_seconds()
            not_unique = []

            while date_ <= end_:
                absence = Absences(date=date_,
                                   user=user,
                                   cause=cause,
                                   credit=credit,
                                   debit=debit,
                                   )
                try:
                    absence.validate_unique(exclude=['cause', 'credit', 'debit'])
                    absence.save()
                except ValidationError:
                    str_date = '{:%d/%m/%Y}'.format(date_)
                    not_unique.append(str_date)
                date_ += timedelta(days=1)

            request.session['not_unique'] = not_unique
            return HttpResponseRedirect(r('absences', username=user.username, year=begin_.year))

        else:
            return render(request, 'newabsence.html', {'form': form})
    else:
        form = AbsencesForm(users=users)
        return render(request, 'newabsence.html', {'form': form})


@login_required
def absences(request, username, year):
    user = get_object_or_404(User, username=username)
    year = int(year)
    absences_ = [x for x in Absences.objects.filter(date__year=year, user=user).all()]
    data = []
    for d in absences_:
        data.append({'date': d.date,
                     'cause': d.get_cause_display(),
                     'credit': timedelta(seconds=d.credit),
                     'debit': timedelta(seconds=d.debit)})
    has_previous_year = bool(Absences.objects.filter(date__year=year-1, user=user))
    has_next_year = bool(Absences.objects.filter(date__year=year+1, user=user))

    previous = year - 1 if has_previous_year else None
    next_ = year + 1 if has_next_year else None

    not_unique = request.session.get('not_unique', [])
    request.session['not_unique'] = []

    return render(request, 'absences.html', {'absences': data,
                                             'username': user.username,
                                             'first_name': user.first_name,
                                             'last_name': user.last_name,
                                             'not_unique': not_unique,
                                             'year': year,
                                             'previous': previous,
                                             'next': next_})


@login_required
def absences_office(request):
    user = request.user
    office = user.userdetail.office
    users = [u.user for u in office.users.all()]
    context = {
        'office': office,
        'user': user,
        'users': users
    }
    return render(request, 'absences_office.html', context)


@login_required
def hours_bank(request):
    """
    Shows the balance of hours of office workers. It must show the balances for yesterday.
    """
    office = request.user.userdetail.office
    users = [u.user for u in office.users.all()]
    today = timezone.localtime(timezone.now()).date()
    yesterday = today - timedelta(days=1)
    date_ = None

    # The 'begin_date' key is present when redirected from calculate_hours_bank
    if 'begin_date' in request.session.keys():
        str_date = request.session['begin_date']
        year = int(str_date.split('-')[0])
        month = int(str_date.split('-')[1])
        day = int(str_date.split('-')[2])
        date_ = date(year, month, day)
        request.session.pop('begin_date')

    # Updates HoursBalance, if needed:
    updates_hours_balance(office, date_)

    # Generates context for template
    lines = []
    for user in users:
        lines.append(
            {'username': user.username,
             'first_name': user.first_name,
             'last_name': user.last_name,
             'balance': HoursBalance.objects.get(
                 date=yesterday,
                 user=user).time_balance()
             }
        )
    return render(request, 'hours_bank.html',
                  {'office': office,
                   'lines': lines}
                  )


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
            if not form_begin or form_begin < start_control:
                begin_date = start_control
            else:
                begin_date = form_begin
            request.session['begin_date'] = str(begin_date)
            return HttpResponseRedirect(r('hours_bank'))
        else:
            return render(request, 'calculate_bank.html', {'form': form})
    else:
        form = GenerateBalanceForm()
        return render(request, 'calculate_bank.html', {'form': form})


@login_required
def my_hours_bank(request, username, year, month):
    user = get_object_or_404(User, username=username)
    start_control_date = user.userdetail.office.hours_control_start_date
    min_valid_date = date(start_control_date.year, start_control_date.month, 1)
    first_day_of_month = date(int(year), int(month), 1)

    if first_day_of_month < min_valid_date:
        return render(request,
                      'nonexistent_balance.html',
                      {'min_valid_year': str(min_valid_date.year),
                       'min_valid_month': str(min_valid_date.month),
                       'min_valid_date': min_valid_date,
                       'first_name': user.first_name,
                       'last_name': user.last_name,
                       'username': username}
                      )
    previous, next_ = previous_next(first_day_of_month, HoursBalance, user)

    lines = UserBalance(user, year=year, month=month).get_monthly_lines()

    return render(request, 'my_hours_bank.html', {'lines': lines,
                                                  'username': username,
                                                  'first_name': user.first_name,
                                                  'last_name': user.last_name,
                                                  'date': first_day_of_month,
                                                  'previous': previous,
                                                  'next': next_})


@login_required
def rules(request):
    office = request.user.userdetail.office
    params = [
        {
        'description': Office._meta.get_field('regular_work_hours').verbose_name,
        'active': True,
        'value': str(office.regular_work_hours)
        },
        {
        'description': Office._meta.get_field('min_work_hours_for_credit').verbose_name,
        'active': office.min_work_hours_for_credit,
        'value': str(office.min_work_hours_for_credit_value)
        },
        {
        'description': Office._meta.get_field('max_daily_credit').verbose_name,
        'active': office.max_daily_credit,
        'value': office.max_daily_credit_value
        },
        {
        'description': Office._meta.get_field('max_monthly_balance').verbose_name,
        'active': office.max_monthly_balance,
        'value': office.max_monthly_balance_value
        },
        {
        'description': Office._meta.get_field('min_checkin_time').verbose_name,
        'active': office.min_checkin_time,
        'value': office.min_checkin_time_value
        },
        {
        'description': Office._meta.get_field('max_checkout_time').verbose_name,
        'active': office.max_checkout_time,
        'value': office.max_checkout_time_value
        },
        {
        'description': Office._meta.get_field('checkin_tolerance').verbose_name,
        'active': True,
        'value': office.checkin_tolerance
        },
        {
        'description': Office._meta.get_field('checkout_tolerance').verbose_name,
        'active': True,
        'value': office.checkout_tolerance
        }
    ]

    return render(request, 'rules.html', {'params': params})


@login_required
def my_tickets(request, username, year, month):
    user = get_object_or_404(User, username=username)
    start_control_date = user.userdetail.office.hours_control_start_date
    min_valid_date = date(start_control_date.year, start_control_date.month, 1)
    first_day_of_month = date(int(year), int(month), 1)
    days_in_month = calendar.monthrange(int(year), int(month))[1]
    last_day_of_month = first_day_of_month + timedelta(days=days_in_month-1)

    if first_day_of_month < min_valid_date:
        return render(request,
                      'nonexistent_tickets.html',
                      {'min_valid_year': str(min_valid_date.year),
                       'min_valid_month': str(min_valid_date.month),
                       'min_valid_date': min_valid_date,
                       'first_name': user.first_name,
                       'last_name': user.last_name,
                       'username': username}
                      )
    # previous, next_ = previous_next(first_day_of_month, Timing, user)

    previous_day = first_day_of_month - timedelta(days=1)
    next_day = last_day_of_month + timedelta(days=1)

    first_datetime_of_month = timezone.make_aware(
        datetime(int(year), int(month), 1, 0, 0, 0)
    )
    last_datetime_of_month = timezone.make_aware(
        datetime(int(year), int(month), days_in_month, 23, 59, 59)
    )

    previous_exists = bool(Timing.objects.filter(
        user=user,
        date_time__lt=first_datetime_of_month)
    )

    next_exists = bool(Timing.objects.filter(
        user=user,
        date_time__gt=last_datetime_of_month)
    )

    previous = None
    next_ = None

    if previous_exists:
        previous = {'year': str(previous_day.year), 'month': str(previous_day.month)}

    if next_exists:
        next_ = {'year': str(next_day.year), 'month': str(next_day.month)}

    tickets_utc = [t for t in Timing.objects.filter(
        user=user,
        date_time__gte=first_datetime_of_month,
        date_time__lte=last_datetime_of_month).order_by('date_time')]

    # The date_time in tickets are stored in UTC. So, let's change them to local time,
    # to avoid problems when extracting dates from date_times.
    # for t in tickets:
    #     t.date_time += utc_offset
    tickets_local = tickets_utc
    for t in tickets_local:
        t.date_time = timezone.localtime(t.date_time)

    dates_ = list(set([t.date_time.date() for t in tickets_local]))

    dates_.sort()

    lines = []
    line = []

    # 'lines' is a list of lists. Each list contains date, checkin datetime and checkout datetime
    for date_ in dates_:
        tkts = [t for t in tickets_local if t.date_time.date() == date_]
        for tkt in tkts:
            if tkt.checkin:
                line.append(date_)
                # line.append(tkt.date_time)
                line.append(tkt)
                if tkt == tkts[-1]:
                    line.append(None)
                    lines.append(line)
                    line = []
            else:
                if len(line) == 0:
                    line.append(date_)
                    line.append(None)
                    # line.append(tkt.date_time)
                    line.append(tkt)
                else:
                    # line.append(tkt.date_time)
                    line.append(tkt)
                lines.append(line)
                line = []

    # Let's transform 'lines' in a list of dictionaries, for rendering in template
    table = []
    for l in lines:
        table.append(
            {
                'date': l[0],
                'check_in': l[1],
                'checkout': l[2]
            }
        )

    return render(request,
                  'my_tickets.html',
                  {'lines': table,
                   'username': username,
                   'first_name': user.first_name,
                   'last_name': user.last_name,
                   'date': first_day_of_month,
                   'previous': previous,
                   'next': next_})


@login_required
def restdays(request, year):
    year = int(year)
    rest_days = [x for x in Restday.objects.filter(date__year=year).all()]
    list_ = []
    for restday in rest_days:
        list_.append(
            {'date': restday.date,
             'note': restday.note,
             'work_hours': restday.work_hours}
        )
    has_previous_year = bool(Restday.objects.filter(date__year=year-1))
    has_next_year = bool(Restday.objects.filter(date__year=year+1))

    previous = year - 1 if has_previous_year else None
    next_ = year + 1 if has_next_year else None

    return render(request, 'restdays.html', {'restdays': list_,
                                             'year': year,
                                             'previous': previous,
                                             'next': next_}
                  )


@login_required
def calculations(request, username, year, month, day):
    user = get_object_or_404(User, username=username)
    date_ = date(int(year), int(month), int(day))
    datedata = DateData(user, date_)
    return render(request, 'calculations.html', {'date': datedata})
