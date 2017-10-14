import datetime

import pytz
from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.models import Timing, Office, Restday, Absences


class MyHoursBankViewTest(TestCase):

    def setUp(self):

        # Let's create a list of days beginning at a monday, at least 'int' days before today (see
        # generate_days_list function).
        self.days = generate_days_list(7)

        self.year = timezone.now().year
        self.month = timezone.now().month
        self.office = Office.objects.create(
            name='Terceira Diacomp',
            initials='DIACOMP3',
            checkin_tolerance=datetime.timedelta(minutes=0),
            checkout_tolerance=datetime.timedelta(minutes=0),
            hours_control_start_date=self.days[0]
        )
        self.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user.first_name = 'ze'
        self.user.last_name = 'mane'
        self.user.save()
        self.user.userdetail.opening_hours_balance = 0
        self.user.userdetail.office = self.office
        self.user.save()
        self.client.login(username='testuser', password='senha123')
        self.resp = self.client.get(r('my_hours_bank', 'testuser', self.year, self.month))

        from gerencex.core.views import UserBalance
        self.first_date = UserBalance(self.user, year=self.year, month=self.month).first_day

    def test_get(self):
        self.assertEqual(200, self.resp.status_code)

    def test_template(self):
        self.assertTemplateUsed(self.resp, 'my_hours_bank.html')

    def test_html(self):
        # activate_timezone()
        tickets = []

        # Let's create the list of check-ins and checkouts
        for d in self.days:
            tickets.append(
                {'date': datetime.datetime(d.year, d.month, d.day, hour=12, minute=0, second=0),
                 'checkin': True}
            )
            tickets.append(
                {'date': datetime.datetime(d.year, d.month, d.day, hour=19, minute=0, second=0),
                 'checkin': False}
            )

        # Today, the user has not checked out yet
        del(tickets[-1])

        # Let's add a restday on the 3rd day:
        d3 = self.days[2]

        Restday.objects.create(
            date=d3,
            note='Feriado de teste',
            work_hours=datetime.timedelta(hours=4)
        )
        tickets[5]['date'] = datetime.datetime(
            d3.year, d3.month, d3.day, hour=15, minute=0, second=0
        )

        # Let's register an absence in the 4th day. The user has checked out earlier,
        # due to medical reasons: Debit = 3 hours
        d4 = self.days[3]
        Absences.objects.create(
            date=d4,
            user=self.user,
            cause='LM',
            credit=0,
            debit=datetime.timedelta(hours=4).seconds
        )
        tickets[7]['date'] = datetime.datetime(
            d4.year, d4.month, d4.day, hour=16, minute=0, second=0
        )

        # Let's register the user's check ins and checkouts
        for ticket in tickets:
            Timing.objects.create(
                user=self.user,
                date_time=timezone.make_aware(ticket['date']),
                checkin=ticket['checkin']
            )

        # Now, let's call the my_hours_bank view for the current month
        self.resp2 = self.client.get(r('my_hours_bank', 'testuser', self.year, self.month))
        line_date = '{:%d/%m/%Y}'.format(self.days[-2])
        line_credit = '7:00:00'
        line_debit = '7:00:00'
        line_balance = '0:00:00'

        contents = [''] if timezone.localtime(timezone.now()).date().day == 1 else \
            [line_date, line_credit, line_debit, line_balance]
        for expected in contents:
            with self.subTest():
                self.assertContains(self.resp2, expected)


def activate_timezone():
    return timezone.activate(pytz.timezone('America/Sao_Paulo'))


def generate_days_list(n):
    """
    :param n: An integer. Indicates the minimum number of days before today, from which the list
    must begin.
    :return: A list of datetime.date elements, beginning at the first monday prior to 'n' days
    before today.
    """
    today = timezone.localtime(timezone.now()).date()
    aux = today - datetime.timedelta(days=n)
    first_monday = aux - datetime.timedelta(days=aux.weekday())
    days = []
    d = first_monday
    while d <= today:
        if d.weekday() not in (5, 6):
            days.append(d)
        d += datetime.timedelta(days=1)
    return days
