import datetime

import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from gerencex.core.models import Timing, Restday, Absences, Office
from gerencex.core.time_calculations import DateData


class TimeCalculationsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Office.objects.create(name='Nenhuma lotação',
                              initials='NL',
                              hours_control_start_date=datetime.date(2016, 9, 1),
                              min_work_hours_for_credit=False
                              )

        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        cls.user = User.objects.get(username='testuser')

    def test_credit(self):
        activate_timezone()
        Timing.objects.create(
             user=self.user,
             date_time=timezone.make_aware(datetime.datetime(2016, 10, 3, 7, 0, 0, 0)),
             checkin=True
        )
        Timing.objects.create(
             user=self.user,
             date_time=timezone.make_aware(datetime.datetime(2016, 10, 3, 21, 0, 0, 0)),
             checkin=False
        )

        credit = DateData(self.user, datetime.date(2016, 10, 3)).credit()
        checkout_tolerance = self.user.userdetail.office.checkout_tolerance
        checkin_tolerance = self.user.userdetail.office.checkin_tolerance
        tolerance = checkout_tolerance + checkin_tolerance

        self.assertEqual(datetime.timedelta(hours=14) + tolerance, credit)

    def test_debit_normal_day(self):
        """
        Normal day:     debit = REGULAR_WORK_HOURS
        """

        debit = DateData(self.user, datetime.date(2016, 10, 10)).debit()
        self.assertEqual(self.user.userdetail.office.regular_work_hours, debit)

    def test_debit_restday(self):
        """
        Restday:        debit = 0
        """
        Restday.objects.create(
            date=datetime.date(2016, 10, 12),
            note='Feriado N. Sª Aparecida',
            work_hours=datetime.timedelta(hours=0)
        )
        debit = DateData(self.user, datetime.date(2016, 10, 12)).debit()
        self.assertEqual(datetime.timedelta(hours=0), debit)

    def test_debit_absence_day(self):
        """
        Absence day:    debit = REGULAR_WORK_HOURS + absence.debit
        """

        Absences.objects.create(
            date=datetime.date(2016, 10, 10),
            user=self.user,
            cause='LM',
            credit=0,
            debit=25200
        )
        debit = DateData(self.user, datetime.date(2016, 10, 10)).debit()
        self.assertEqual(datetime.timedelta(hours=0), debit)


def activate_timezone():
    return timezone.activate(pytz.timezone('America/Sao_Paulo'))
