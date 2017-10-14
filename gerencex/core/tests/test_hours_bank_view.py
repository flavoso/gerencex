import datetime

import pytz
from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.models import Timing, Office, Restday, Absences


class HoursBankViewTest(TestCase):

    def setUp(self):

        # Let's create a list of days beginning at a monday, at least 'int' days before today (see
        # generate_days_list function).
        self.days1 = generate_days_list(7, (5, 6))
        self.days2 = generate_days_list(7, (6, ))
        self.year = timezone.now().year
        self.month = timezone.now().month
        self.office = Office.objects.create(
            name='Terceira Diacomp',
            initials='DIACOMP3',
            checkin_tolerance=datetime.timedelta(minutes=0),
            checkout_tolerance=datetime.timedelta(minutes=0),
            hours_control_start_date=self.days1[0]
        )

        # Our test needs two users...
        self.user1 = User.objects.create_user('testuser1', 'test1@user.com', 'senha123')
        self.user1.first_name = 'lazy'
        self.user1.last_name = 'guy'
        self.user1.save()
        self.user1.userdetail.opening_hours_balance = 0
        self.user1.userdetail.office = self.office
        self.user1.save()

        self.user2 = User.objects.create_user('testuser2', 'test2@user.com', 'senha123')
        self.user2.first_name = 'poor'
        self.user2.last_name = 'worker'
        self.user2.save()
        self.user2.userdetail.opening_hours_balance = 0
        self.user2.userdetail.office = self.office
        self.user2.save()

        # Let's create the list of check-ins and checkouts for user1, who did not
        # work on weekend
        tickets1 = []
        for d in self.days1:
            tickets1.append(
                {'date': datetime.datetime(d.year, d.month, d.day, hour=12, minute=0, second=0),
                 'checkin': True}
            )
            tickets1.append(
                {'date': datetime.datetime(d.year, d.month, d.day, hour=19, minute=0, second=0),
                 'checkin': False}
            )

        # Let's create the list of check-ins and checkouts for user2, who worked
        # on saturdays
        tickets2 = []
        for d in self.days2:
            tickets2.append(
                {'date': datetime.datetime(d.year, d.month, d.day, hour=12, minute=0, second=0),
                 'checkin': True}
            )
            tickets2.append(
                {'date': datetime.datetime(d.year, d.month, d.day, hour=19, minute=0, second=0),
                 'checkin': False}
            )

        # Let's delete the tickets for yesterday from tickets2 list. This is
        # to reproduce the conditions of a bug. When some workers work on
        # weekend, the hours_bank view crashes with a 500 error code.

        del(tickets2[-1])
        del(tickets2[-1])

        # Let's register the user's check ins and checkouts
        for ticket in tickets1:
            Timing.objects.create(
                user=self.user1,
                date_time=timezone.make_aware(ticket['date']),
                checkin=ticket['checkin']
            )

        for ticket in tickets2:
            Timing.objects.create(
                user=self.user2,
                date_time=timezone.make_aware(ticket['date']),
                checkin=ticket['checkin']
            )

        # Let's make user1's login and access the hours_bank view

        self.client.login(username='testuser1', password='senha123')
        self.resp = self.client.get(r('hours_bank'))

    def test_get(self):
        self.assertEqual(200, self.resp.status_code)

    def test_template(self):
        self.assertTemplateUsed(self.resp, 'hours_bank.html')

    def test_html(self):
        contents = ['Lazy Guy', '0:00:00',
                    'Poor Worker']
        for expected in contents:
            with self.subTest():
                self.assertContains(self.resp, expected)


def generate_days_list(n, excluded_days):
    """
    :param n: An integer. Indicates the minimum number of days before today, from which the list
    must begin.
    :param excluded_days: A tuple with the weekdays to exclude from list.
    Ex: (5, 6) excludes saturdays and sundays
    :return: A list of datetime.date elements, beginning at the first monday prior to 'n' days
    before today, and ending in the following sunday.
    """
    today = timezone.localtime(timezone.now()).date()
    aux = today - datetime.timedelta(days=n)
    first_monday = aux - datetime.timedelta(days=aux.weekday())
    days = []
    d = first_monday
    while d < today:
        if d.weekday() not in excluded_days:
            days.append(d)
        d += datetime.timedelta(days=1)
    return days
