import calendar
from datetime import timedelta, date

from django.utils import timezone
from gerencex.core.models import Restday, Absences, HoursBalance
from gerencex.core.time_calculations import DateData


def dates(date1, date2):
    """
    :param date1: begin date
    :param date2: end date
    :return: all dates between date1 and (date2 - 1)
    """
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
        today = timezone.localtime(timezone.now()).date()
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        first_month_day = date(self.year, self.month, 1)
        self.last_month_day = first_month_day + timedelta(days=days_in_month)
        self.last_day = min(today, self.last_month_day)
        self.start_date = user.userdetail.office.hours_control_start_date

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
                    credit=DateData(self.user, date_).credit().total_seconds(),
                    debit=DateData(self.user, date_).debit().total_seconds()
                )

            line = HoursBalance.objects.get(user=self.user, date=date_)

            lines.append({'date': date_,
                          'credit': line.time_credit(),
                          'debit': line.time_debit(),
                          'balance': line.time_balance(),
                          'comment': comments(self.user, date_)})
        return lines

    def create_or_update_line(self, date_):
        credit = DateData(self.user, date_).credit().total_seconds()
        debit = DateData(self.user, date_).debit().total_seconds()
        updated_values = {'credit': credit, 'debit': debit}
        HoursBalance.objects.update_or_create(
            date=date_,
            user=self.user,
            defaults=updated_values
        )


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


def previous_next(date_, model, user):
    first_day_of_month = date(date_.year, date_.month, 1)
    try_previous = first_day_of_month - timedelta(days=1)
    try_next = first_day_of_month + timedelta(days=31)

    previous_exists = model.objects.filter(date__year=try_previous.year,
                                           date__month=try_previous.month,
                                           user=user)

    next_exists = model.objects.filter(date__year=try_next.year,
                                       date__month=try_next.month,
                                       user=user)

    previous = None
    next_ = None

    if previous_exists:
        previous = {'year': str(try_previous.year), 'month': str(try_previous.month)}

    if next_exists:
        next_ = {'year': str(try_next.year), 'month': str(try_next.month)}

    return previous, next_


def updates_hours_balance(office, date_):
    """
    Calculates the hour balances of all workers in an office, from a given date up until yesterday
    :param date_: the begin date for updating
    :param office: the workers' office
    :return: Nothing. It just updates the database
    """
    users = [x.user for x in office.users.all()]
    today = timezone.localtime(timezone.now()).date()

    # date_ is present if calculate_hours_bank view was triggered. In this case, we must update
    # or create the balances for all office workers, and for all dates between date_ and today
    if date_:
        for d in dates(date_, today):
            for user in users:
                updated_values = {
                    'credit': DateData(user, d).credit().total_seconds(),
                    'debit': DateData(user, d).debit().total_seconds()
                }
                HoursBalance.objects.update_or_create(
                    date=d,
                    user=user,
                    defaults=updated_values
                )

    # date_ is not present when we just want to see hours_bank. In this case, we must check if
    # all office users have balances for yesterday, filling the blanks.
    else:
        for user in users:
            last_user_balance_date = HoursBalance.objects.filter(user=user).last().date
            next_user_balance_date = last_user_balance_date + timedelta(days=1)
            if next_user_balance_date < today:
                for d in dates(next_user_balance_date, today):
                    HoursBalance.objects.create(
                        date=d,
                        user=user,
                        credit=DateData(user, d).credit().total_seconds(),
                        debit=DateData(user, d).debit().total_seconds()
                    )

    office.last_balance_date = today
    office.save()
