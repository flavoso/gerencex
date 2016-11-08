import datetime

import pytz
from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.forms import RestdayForm
from gerencex.core.models import UserDetail, Timing, Restday, HoursBalance, Absences, Office
from gerencex.core.time_calculations import calculate_credit, calculate_debit


class LogIn(TestCase):

    def setUp(self):
        self.response = self.client.get(r('login'))

    def test_get(self):
        """GET must return status code 200"""
        self.assertEqual(200, self.response.status_code)

    def test_template(self):
        """Must use registration/index.html"""
        self.assertTemplateUsed(self.response, 'registration/login.html')


class HomeTest(TestCase):

    def setUp(self):
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.client.login(username='testuser', password='senha123')
        self.response = self.client.get(r('home'), follow=True)

    def test_get(self):
        """GET must return status code 200"""
        self.assertEqual(200, self.response.status_code)

    def test_template(self):
        """Must use index.html"""
        self.assertTemplateUsed(self.response, 'index.html')


class NotFound(TestCase):

    def setUp(self):
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.client.login(username='testuser', password='senha123')
        self.response = self.client.get('/nao-encontrada/')

    def test_get(self):
        """GET must return status code 404"""
        self.assertEqual(404, self.response.status_code)

    def test_template(self):
        """Must use registration/index.html"""
        self.assertTemplateUsed(self.response, '404.html')


class LogOut(TestCase):

    def setUp(self):
        self.response = self.client.get(r('logout'), follow=True)
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.client.login(username='testuser', password='senha123')

    def test_get(self):
        """GET must return status code 200"""
        self.assertEqual(200, self.response.status_code)

    def test_template(self):
        """Must use index.html"""
        self.assertTemplateUsed(self.response, 'registration/login.html')


class UserDetailTest(TestCase):

    def setUp(self):
        Office.objects.create(name='Nenhuma lotação',
                              initials='NL')
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user = User.objects.get(username='testuser')
        # UserDetail.objects.create(user=self.user)

    def test_userdetail_create(self):
        """
        User must have default values for 'atwork' (False) and office ('Nenhuma lotação')
        """
        atwork = self.user.userdetail.atwork
        office = self.user.userdetail.office.initials
        self.assertFalse(atwork)
        self.assertEqual('NL', office)

    def test_userdetail_save(self):
        """
        User must have default values for 'atwork' (False) and office ('Nenhuma lotação')
        """
        user2 = User(username='testuser2',
                     email='test2@user.com',
                     password='senha321')
        user2.save()
        atwork = user2.userdetail.atwork
        office = user2.userdetail.office.initials
        self.assertFalse(atwork)
        self.assertEqual('NL', office)


class TimingViewTest(TestCase):

    def setUp(self):
        Office.objects.create(name='Nenhuma lotação', initials='NL')
        self.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
        # self.userdetail = UserDetail.objects.create(user=self.user)
        self.client.login(username='testuser', password='senha123')

    def test_get(self):
        self.response = self.client.get(r('timing_new'))
        self.assertEqual(200, self.response.status_code)
        self.assertTemplateUsed(self.response, 'timing_new_not_post.html')

    def test_valid_checkin(self):
        """Valid checkin: (a) redirects to 'timing'; b) changes userdetail.atwork to True; (c)
        generates a checkin ticket; (d) the ticket is created by the user"""
        self.user.userdetail.atwork = False
        self.user.save()
        self.response = self.client.post(r('timing_new'))
        self.assertRedirects(self.response, r('timing', 1))

        atwork = UserDetail.objects.get(user=self.user).atwork
        self.assertTrue(atwork)

        checkin_tickets = Timing.objects.filter(user=self.user, checkin=True).all()
        self.assertEqual(len(checkin_tickets), 1)

        created_by = checkin_tickets[0].created_by
        self.assertEqual(created_by, self.user)

    def test_valid_checkout(self):
        """Valid checkout: (a) occurs only when there is a checkin at the same day; b) redirects
        to 'timing'; (c) changes userdetail.atwork to False; (d) generates a checkout ticket;
        (e) the ticket is created by the user"""
        activate_timezone()
        d = datetime.datetime.now() + datetime.timedelta(hours=-1)
        date_time = timezone.make_aware(d)
        Timing.objects.create(user=self.user, date_time=date_time, checkin=True,
                              created_by=self.user)
        self.user.userdetail.atwork = True
        self.user.save()
        self.response = self.client.post(r('timing_new'))
        self.assertRedirects(self.response, r('timing', 2))

        atwork = UserDetail.objects.get(user=self.user).atwork
        self.assertFalse(atwork)

        checkout_tickets = Timing.objects.filter(user=self.user, checkin=False)
        self.assertEqual(len(checkout_tickets), 1)

        created_by = checkout_tickets[0].created_by
        self.assertEqual(created_by, self.user)

    def test_invalid_checkout(self):
        """Invalid checkout: (a) occurs when the last checkin didn't happen in the same day
        before; b) redirects to 'timing', with an alert message; (c) changes userdetail.atwork to
        False; (d) doesn't generate a checkout ticket"""
        activate_timezone()
        d = datetime.datetime.now() + datetime.timedelta(days=-1)
        date_time = timezone.make_aware(d)
        Timing.objects.create(user=self.user, date_time=date_time, checkin=True,
                              created_by=self.user)
        self.user.userdetail.atwork = True
        self.user.save()
        self.response = self.client.post(r('timing_new'))
        self.assertRedirects(self.response, r('timing_fail'))

        atwork = UserDetail.objects.get(user=self.user).atwork
        self.assertFalse(atwork)


class ForgottenCheckoutsViewTest(TestCase):

    def setUp(self):
        Office.objects.create(name='Nenhuma lotação', initials='NL')
        self.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user.first_name = 'ze mane'
        self.user.save()
        self.client.login(username='testuser', password='senha123')

    def test_get(self):
        self.resp = self.client.get(r('forgotten_checkouts'))
        self.assertEqual(200, self.resp.status_code)

    def test_template(self):
        self.resp = self.client.get(r('forgotten_checkouts'))
        self.assertTemplateUsed(self.resp, 'forgotten_checkouts.html')

    def test_html(self):
        activate_timezone()

        d1 = datetime.datetime.now() + datetime.timedelta(days=-3)
        date_time_1 = timezone.make_aware(d1)
        d2 = datetime.datetime.now() + datetime.timedelta(days=-2)
        date_time_2 = timezone.make_aware(d2)
        d3 = datetime.datetime.now() + datetime.timedelta(days=-1)
        date_time_3 = timezone.make_aware(d3)
        d4 = datetime.datetime.now()
        date_time_4 = timezone.make_aware(d4)

        Timing.objects.create(user=self.user, date_time=date_time_1, checkin=False,
                              created_by=self.user)
        Timing.objects.create(user=self.user, date_time=date_time_2, checkin=True,
                              created_by=self.user)
        Timing.objects.create(user=self.user, date_time=date_time_3, checkin=True,
                              created_by=self.user)

        pk = Timing.objects.get(date_time=date_time_2).pk
        self.resp = self.client.get(r('forgotten_checkouts'))

        expected = '<td>' + str(pk) + '</td>'

        self.assertContains(self.resp, expected)


class TimingModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')

    def setUp(self):
        self.client.login(username='testuser', password='senha123')

    def test_create(self):
        t = Timing.objects.create(
            user=self.user,
            date_time=timezone.make_aware(datetime.datetime(2016, 10, 19, 7, 0, 0, 0))
        )                                                   # 'checkin' defaults to 'False'
        self.assertTrue(Timing.objects.exists())

        default_values = (t.checkin, t.created_by)
        self.assertTupleEqual((True, None), default_values)


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


class AbsencesModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')

    def test_create(self):
        Absences.objects.create(
            date=datetime.date(2016, 9, 5),
            user=self.user,
            cause='curso',
            credit=25200,
            debit=0
        )

        self.assertTrue(Absences.objects.exists())


class TimeCalculationsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Office.objects.create(name='Nenhuma lotação',
                              initials='NL',
                              hours_control_start_date=datetime.date(2016, 9, 1))
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

        credit = calculate_credit(self.user, datetime.date(2016, 10, 3))
        checkout_tolerance = self.user.userdetail.office.checkout_tolerance
        checkin_tolerance = self.user.userdetail.office.checkin_tolerance
        tolerance = checkout_tolerance + checkin_tolerance

        self.assertEqual(datetime.timedelta(hours=14) + tolerance, credit)

    def test_debit_normal_day(self):
        """
        Normal day:     debit = REGULAR_WORK_HOURS
        """

        debit = calculate_debit(self.user, datetime.date(2016, 10, 10))
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
        debit = calculate_debit(self.user, datetime.date(2016, 10, 12))
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
        debit = calculate_debit(self.user, datetime.date(2016, 10, 10))
        self.assertEqual(datetime.timedelta(hours=0), debit)


class CreditTriggerTest(TestCase):
    """
    The user credit is always registered at HourBalance via signal, when a checkout occurs.
    See the 'credit_calculation' function, at signals.py
    """
    @classmethod
    def setUpTestData(cls):
        Office.objects.create(name='Nenhuma lotação', initials='NL')
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        cls.user = User.objects.get(username='testuser')

    def test_credit_triggers(self):
        activate_timezone()
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


class CalculateHoursBankViewTest(TestCase):

    def setUp(self):
        # Let's create a list of days beginning at a monday, at least 'n' days before today (see
        # generate_days_list function).
        self.days = generate_days_list(7)

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
        self.resp = self.client.get(r('calculate_hours_bank'), follow=True)

    def test_get(self):
        self.assertEqual(200, self.resp.status_code)

    def test_template(self):
        self.assertTemplateUsed(self.resp, 'calculate_bank.html')

    def test_post(self):
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

        # Let's add a restday on the 3rd day:
        d3 = self.days[2]

        Restday.objects.create(
            date=d3,
            note='Feriado de teste',
            work_hours=datetime.timedelta(hours=4)
        )
        tickets[5]['date'] = datetime.datetime(
            d3.year, d3.month, d3.day, hour=16, minute=0, second=0
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
        #                                      line.time_debit(),
        #                                      line.time_credit(),
        #                                      line.time_balance()
        #                                      ))
        # print(self.resp2.content)
        for expected in contents:
            with self.subTest():
                self.assertContains(self.resp2, expected)


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

        # Today, the user has not checked out yet
        del(tickets[-1])
        #
        # # Let's add a restday on the 3rd day:
        # d3 = self.days[2]
        #
        # Restday.objects.create(
        #     date=d3,
        #     note='Feriado de teste',
        #     work_hours=datetime.timedelta(hours=4)
        # )
        # tickets[5]['date'] = datetime.datetime(
        #     d3.year, d3.month, d3.day, hour=15, minute=0, second=0
        # )
        #
        # # Let's register an absence in the 4th day. The user has checked out earlier,
        # # due to medical reasons: Debit = 3 hours
        # d4 = self.days[3]
        # Absences.objects.create(
        #     date=d4,
        #     user=self.user,
        #     cause='LM',
        #     credit=0,
        #     debit=datetime.timedelta(hours=4).seconds
        # )
        # tickets[7]['date'] = datetime.datetime(
        #     d4.year, d4.month, d4.day, hour=16, minute=0, second=0
        # )

        # Let's register the user's check ins and checkouts
        for ticket in tickets:
            Timing.objects.create(
                user=self.user,
                date_time=timezone.make_aware(ticket['date']),
                checkin=ticket['checkin']
            )

        # Now, let's call the my_hours_bank view for the current month
        self.resp2 = self.client.get(r('my_hours_bank', 'testuser', self.year, self.month))
        line = HoursBalance.objects.filter(user=self.user).last()
        line_date = '<td>{:%d/%m/%Y}</td>'.format(self.days[-2])
        line_credit = '<td>7:00:00</td>'
        line_debit = '<td>7:00:00</td>'
        line_balance = '<td>0:00:00</td>'
        contents = [line_date, line_credit, line_debit, line_balance]
        # line = "\n".join([x for x in contents])
        # # print(self.resp2.content)
        # self.assertContains(self.resp2, line)
        for expected in contents:
            with self.subTest():
                self.assertContains(self.resp2, expected)

        # line = HoursBalance.objects.filter(date=self.first_date, user=self.user).last()
        #
        # print('Data: {}'.format(line.date))
        # print('Crédito: ' + str(line.credit))
        # print('Débito: ' + str(line.debit))
        # print('Saldo: ' + str(line.balance))

        # from gerencex.core.views import comments
        # print('Observação: {}'.format(comments(self.user, self.first_date)))

        # Now, let's call the my_hours_bank view for the initial month
        # self.resp3 = self.client.get(r('my_hours_bank',
        #                                'testuser',
        #                                self.days[0].year,
        #                                self.days[0].month))
        #
        # line = HoursBalance.objects.filter(date=self.days[0], user=self.user).last()

        # print('Data: {}'.format(line.date))
        # print('Crédito: {}'.format(line.credit))
        # print('Débito: {}'.format(line.debit))
        # print('Saldo: {}'.format(line.balance))
        # print('Crédito: {}'.format(line.time_credit()))
        # print('Débito: {}'.format(line.time_debit()))
        # print('Saldo: {}'.format(line.time_balance()))

        # from gerencex.core.views import comments
        # print('Observação: {}'.format(comments(self.user, self.days[0])))

        # print('Resultado do calculate_debit: {}'.format(calculate_debit(self.user, self.days[0])))

        # print('Carga horária: {}'.format(office.regular_work_hours))
        # print('Last Balance Date: {}'.format(office.last_balance_date))
        # print(self.resp2.content)

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
