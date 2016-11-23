import datetime

import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.shortcuts import resolve_url as r
from gerencex.core.models import Office, Timing


class MyTicketsViewTest(TestCase):
    def setUp(self):
        self.days = generate_days_list(5)
        self.office = Office.objects.create(
            name='Terceira Diacomp',
            initials='DIACOMP3',
            checkin_tolerance=datetime.timedelta(minutes=0),
            checkout_tolerance=datetime.timedelta(minutes=0),
            hours_control_start_date=self.days[0]
        )
        self.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user.userdetail.office = self.office
        self.user.save()
        self.client.login(username='testuser', password='senha123')
        today = timezone.now().date()
        self.year = today.year
        self.month = today.month
        self.resp = self.client.get(r('my_tickets', self.user.username, self.year, self.month))

    def test_get(self):

        self.assertEqual(200, self.resp.status_code)

    def test_template_used(self):
        self.assertTemplateUsed(self.resp, 'my_tickets.html')

    def test_html_content(self):
        activate_timezone()
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

        # Let's register the user's check ins and checkouts
        for ticket in tickets:
            Timing.objects.create(
                user=self.user,
                date_time=timezone.make_aware(ticket['date']),
                checkin=ticket['checkin']
            )

        resp2 = self.client.get(r('my_tickets', self.user.username, self.year, self.month))

        date = '15/11/2016'
        chk_in = '12:00:00'
        chk_out = '12:00:00'

        self.assertContains(resp2, date, count=2)
        self.assertContains(resp2, chk_in, count=6)
        self.assertContains(resp2, chk_out, count=6)


def activate_timezone():
    return timezone.activate(pytz.timezone('America/Sao_Paulo'))


def generate_days_list(n):
    """
    :param n: An integer. Indicates the minimum number of days before today, from which the list
    must begin.
    :return: A list of datetime.date elements, beginning at the first monday prior to 'n' days
    before today.
    """
    today = datetime.date(2016, 11, 15)
    first_day = today - datetime.timedelta(days=n)
    # aux = today - datetime.timedelta(days=n)
    # first_monday = aux - datetime.timedelta(days=aux.weekday())
    days = []
    d = first_day
    while d <= today:
        days.append(d)
        d += datetime.timedelta(days=1)
    return days
