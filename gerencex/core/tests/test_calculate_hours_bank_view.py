import datetime

import pytz
from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.models import Timing, Restday, Absences, Office, HoursBalance

current_tz = timezone.get_current_timezone()


class CalculateHoursBankViewTest(TestCase):

    def setUp(self):
        # Let's create a list of days beginning at a monday, at least 'n' days before today (see
        # generate_days_list function).
        self.days = generate_days_list(7)

        self.office = Office.objects.create(
            name='Terceira Diacomp',
            initials='DIACOMP3',
            regular_work_hours=datetime.timedelta(hours=6),
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
        self.resp = self.client.get(r('calculate_hours_bank'), follow=True)

    def test_get(self):
        self.assertEqual(200, self.resp.status_code)

    def test_template(self):
        self.assertTemplateUsed(self.resp, 'calculate_bank.html')

    def test_post(self):
        utc = pytz.timezone('UTC')
        tickets = []

        # Let's create the list of check-ins and checkouts

        for d in self.days:
            tickets.append(
                {'date': timezone.make_aware(
                    datetime.datetime(d.year, d.month, d.day, hour=12, minute=0, second=0)
                ),
                 'checkin': True}
            )
            tickets.append(
                {'date': timezone.make_aware(
                    datetime.datetime(d.year, d.month, d.day, hour=18, minute=30, second=0)
                ),
                 'checkin': False}
            )

        # Let's add a restday on the 3rd day:
        d3 = self.days[2]

        Restday.objects.create(
            date=d3,
            note='Feriado de teste',
            work_hours=datetime.timedelta(hours=4)
        )
        tickets[5]['date'] = timezone.make_aware(datetime.datetime(
            d3.year, d3.month, d3.day, hour=16, minute=0, second=0)
        )

        # Let's register an absence in the 4th day. The user has checked out earlier,
        # due to medical reasons: Debit = 3 hours
        d4 = self.days[3]
        Absences.objects.create(
            date=d4,
            user=self.user,
            cause='LM',
            credit=0,
            debit=datetime.timedelta(hours=3).seconds
        )
        tickets[7]['date'] = timezone.make_aware(datetime.datetime(
            d4.year, d4.month, d4.day, hour=15, minute=0, second=0),
        )

        # Let's register the user's check ins and checkouts
        for ticket in tickets:
            Timing.objects.create(
                user=self.user,
                date_time=ticket['date'].astimezone(utc),
                checkin=ticket['checkin']
            )

        # Now, let's call the calculate_hours_bank view
        self.resp2 = self.client.post(r('calculate_hours_bank'), follow=True)
        self.assertEqual(200, self.resp2.status_code)
        self.assertRedirects(self.resp2, r('hours_bank'))
        self.assertTemplateUsed(self.resp2, 'hours_bank.html')

        contents = [
            'Ze Mane',
            '0:00:00'
        ]
        # lines = HoursBalance.objects.filter(user=self.user).all()
        # for line in lines:
        #     print('{} | {} | {} | {}'.format(line.date,
        #                                      line.time_credit(),
        #                                      line.time_debit(),
        #                                      line.time_balance()
        #                                      ))
        # print(self.resp2.content)
        for expected in contents:
            with self.subTest():
                self.assertContains(self.resp2, expected)

        # Now, let's recalculate the hours:
        self.client.session['begin_date'] = str(self.days[3])
        self.resp3 = self.client.post(r('calculate_hours_bank'), follow=True)
        for expected in contents:
            with self.subTest():
                self.assertContains(self.resp3, expected)


def generate_days_list(n):
    """
    :param n: An integer. Indicates the minimum number of days before today, from which the list
    must begin.
    :return: A list of datetime.date elements, beginning at the first monday prior to 'n' days
    before today.
    """
    today = timezone.now().date()
    aux = today - datetime.timedelta(days=n)
    first_monday = aux - datetime.timedelta(days=aux.weekday())
    days = []
    d = first_monday
    while d <= today:
        if d.weekday() not in (5, 6):
            days.append(d)
        d += datetime.timedelta(days=1)
    return days
