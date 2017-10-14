import datetime

import pytz
from django.utils import timezone
from django.contrib.auth.models import User
from django.test import TestCase
from gerencex.core.models import HoursBalance, Timing, Office
from gerencex.core.time_calculations import DateData


class HoursBalanceModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')

    def test_balances(self):
        r1 = HoursBalance.objects.create(
            date=datetime.date(2016, 8, 18),
            user=self.user,
            credit=datetime.timedelta(hours=6).seconds,
            debit=datetime.timedelta(hours=7).seconds,
        )

        # Test creation
        self.assertTrue(HoursBalance.objects.exists())

        # First balance is calculated without a previous balance (see the
        # total_balance_handler function at signals.py)
        self.assertEqual(r1.balance, int(datetime.timedelta(hours=-1).total_seconds()))

        # Second balance takes the first balance into account (see the
        # total_balance_handler function at signals.py)
        r2 = HoursBalance.objects.create(
            date=datetime.date(2016, 8, 19),
            user=self.user,
            credit=datetime.timedelta(hours=6).seconds,
            debit=datetime.timedelta(hours=7).seconds,
        )
        self.assertEqual(r2.balance, int(datetime.timedelta(hours=-2).total_seconds()))

        # Change in first credit or debit must change the second balance (see the
        # next_balance_handler function at signals.py)

        r1.credit = datetime.timedelta(hours=7).seconds
        r1.save()
        r2 = HoursBalance.objects.get(pk=2)
        self.assertEqual(r2.balance, int(datetime.timedelta(hours=-1).total_seconds()))


class CreditTriggerTest(TestCase):
    """
    The user credit is always registered at HourBalance via signal, when a checkout occurs.
    See the 'credit_calculation' function, at signals.py
    """
    @classmethod
    def setUpTestData(cls):
        Office.objects.create(name='Nenhuma lotação',
                              initials='NL',
                              regular_work_hours=datetime.timedelta(hours=6))
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        cls.user = User.objects.get(username='testuser')

    def test_credit_triggers(self):

        # Let's record a check in...
        t1 = Timing.objects.create(
             user=self.user,
             date_time=timezone.make_aware(datetime.datetime(2016, 10, 3, 12, 0, 0, 0)),
             checkin=True
        )

        # ...and a checkout
        t2 = Timing.objects.create(
             user=self.user,
             date_time=timezone.make_aware(datetime.datetime(2016, 10, 3, 13, 0, 0, 0)),
             checkin=False
        )

        # Let's record a balance line at HoursBalance
        date = datetime.date(2016, 10, 3)
        new_credit = DateData(self.user, date).credit().seconds
        new_debit = DateData(self.user, date).debit().seconds
        HoursBalance.objects.create(
            date=date,
            user=self.user,
            credit=new_credit,
            debit=new_debit
        )

        # Let's change t2 (checkout record)
        t2.date_time += datetime.timedelta(hours=1)
        t2.save()

        # The balance must have been recalculated via django signal (signals.py)
        checkout_tolerance = self.user.userdetail.office.checkout_tolerance
        checkin_tolerance = self.user.userdetail.office.checkin_tolerance
        tolerance = checkout_tolerance + checkin_tolerance
        reference = datetime.timedelta(hours=2).seconds + tolerance.seconds
        line = HoursBalance.objects.first()
        credit = line.credit

        self.assertEqual(reference, credit)

        # Let's change t1 (checkin record)
        t1.date_time += datetime.timedelta(hours=1)
        t1.save()

        # The balance must have been recalculated via signal
        modified_reference = datetime.timedelta(hours=1).seconds + tolerance.seconds
        modified_balance_line = HoursBalance.objects.first()
        modified_credit = modified_balance_line.credit

        self.assertEqual(modified_reference, modified_credit)


# TODO: Escrever o teste depois que já houver view para produzir o balanço da divisão e do usuário

class RestdayDebitTriggerTest(TestCase):
    """
    When a we record a Restday whose date is prior to the date of the Balance, the balances must
    be recalculated for all users.
    """
    @classmethod
    def setUpTestData(cls):
        Office.objects.create(name='Diacomp 1', initials='diacomp1')
        Office.objects.create(name='Diacomp 2', initials='diacomp2')
        cls.diacomp1 = Office.objects.get(initials='diacomp1')
        cls.diacomp2 = Office.objects.get(initials='diacomp2')
        cls.diacomp1.hours_control_start_date = datetime.date(2016, 9, 1)
        cls.diacomp1.save()
        cls.diacomp2.hours_control_start_date = datetime.date(2016, 10, 1)
        cls.diacomp1.save()
        User.objects.create_user('testuser1', 'test1@user.com', 'senha123')
        User.objects.create_user('testuser2', 'test2@user.com', 'senha123')
        cls.user1 = User.objects.get(username='testuser')
        cls.user2 = User.objects.get(username='testuser')

    # def test_debit_trigger(self):


def activate_timezone():
    return timezone.activate(pytz.timezone('America/Sao_Paulo'))
