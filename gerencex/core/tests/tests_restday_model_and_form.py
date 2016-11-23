import datetime

import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from gerencex.core.forms import RestdayForm
from gerencex.core.models import Restday, HoursBalance


class RestdayModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.date = Restday.objects.create(
            date=datetime.date(2016, 8, 4),
            note='Jogos olímpicos',
            work_hours=datetime.timedelta(0)
        )

    def test_create(self):
        self.assertTrue(Restday.objects.exists())


class RestdayFormTest(TestCase):

    def test_form_has_fields(self):
        """Form must have 2 fields"""
        form = RestdayForm()
        expected = ('date', 'note', 'work_hours')
        self.assertSequenceEqual(expected, list(form.fields))

    def test_weekend_raises_error(self):
        """Weekends raise error in the form"""
        weekend = datetime.date(2016, 8, 6)
        form = self.make_validated_form(date=weekend)
        self.assertFormErrorCode(form, 'date', 'weekend')

    def assertFormErrorCode(self, form, field, code):
        errors = form.errors.as_data()
        errors_list = errors[field]
        exception = errors_list[0]
        self.assertEqual(code, exception.code)

    def make_validated_form(self, **kwargs):
        valid = dict(date=datetime.date(2016, 8, 5),
                     note='Jogos olímpicos')
        data = dict(valid, **kwargs)
        form = RestdayForm(data)
        form.is_valid()

        return form


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


def activate_timezone():
    return timezone.activate(pytz.timezone('America/Sao_Paulo'))
