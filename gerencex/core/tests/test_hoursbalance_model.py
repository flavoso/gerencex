import datetime

import pytz
from django.utils import timezone
from django.contrib.auth.models import User
from django.test import TestCase
from gerencex.core.models import HoursBalance, Timing, Office


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

        # First balance is calculated without a previous balance
        self.assertEqual(r1.balance, int(datetime.timedelta(hours=-1).total_seconds()))

        # Second balance takes the first balance into account
        r2 = HoursBalance.objects.create(
            date=datetime.date(2016, 8, 19),
            user=self.user,
            credit=datetime.timedelta(hours=6).seconds,
            debit=datetime.timedelta(hours=7).seconds,
        )
        self.assertEqual(r2.balance, int(datetime.timedelta(hours=-2).total_seconds()))

        # Change in first credit or debit must change the second balance

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
        # activate_timezone()
        t1 = Timing.objects.create(
             user=self.user,
             date_time=timezone.make_aware(datetime.datetime(2016, 10, 3, 12, 0, 0, 0)),
             checkin=True
        )

        # Test checkout creation
        t2 = Timing.objects.create(
             user=self.user,
             date_time=timezone.make_aware(datetime.datetime(2016, 10, 3, 13, 0, 0, 0)),
             checkin=False
        )
        date = datetime.date(2016, 10, 3)
        balance_line = HoursBalance.objects.filter(date=date, user=self.user)[0]
        checkout_tolerance = self.user.userdetail.office.checkout_tolerance
        checkin_tolerance = self.user.userdetail.office.checkin_tolerance
        tolerance = checkout_tolerance + checkin_tolerance
        reference = datetime.timedelta(hours=1).seconds + tolerance.seconds
        credit = balance_line.credit

        self.assertEqual(reference, credit)

        # Test checkout change
        t2.date_time += datetime.timedelta(hours=1)
        t2.save()
        modified_reference1 = datetime.timedelta(hours=2).seconds + tolerance.seconds
        modified_balance_line1 = HoursBalance.objects.filter(date=date, user=self.user)[0]
        modified_credit1 = modified_balance_line1.credit

        self.assertEqual(modified_reference1, modified_credit1)

        # Test checkin change
        t1.date_time += datetime.timedelta(hours=1)
        t1.save()
        modified_reference2 = datetime.timedelta(hours=1).seconds + tolerance.seconds
        modified_balance_line2 = HoursBalance.objects.filter(date=date, user=self.user)[0]
        modified_credit2 = modified_balance_line2.credit

        self.assertEqual(modified_reference2, modified_credit2)

        # Test new checkin (in this case, we must not have a corresponding line at HoursBalance)
        t3 = Timing.objects.create(
             user=self.user,
             date_time=timezone.make_aware(datetime.datetime(2016, 10, 3, 14, 0, 0, 0)),
             checkin=True
        )
        modified_reference3 = datetime.timedelta(hours=1).seconds + tolerance.seconds
        modified_balance_line3 = HoursBalance.objects.filter(date=date, user=self.user)[0]
        modified_credit3 = modified_balance_line3.credit

        self.assertEqual(modified_reference3, modified_credit3)


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