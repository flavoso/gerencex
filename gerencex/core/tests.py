import datetime

import pytz
from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.forms import RestdayForm
from gerencex.core.models import UserDetail, Timing, Restday


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

     def test_get(self):
         """GET must return status code 200"""
         self.assertEqual(200, self.response.status_code)

     def test_template(self):
         """Must use index.html"""
         self.assertTemplateUsed(self.response, 'registration/login.html')


class UserDetailTest(TestCase):

    def setUp(self):
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user = User.objects.get(username='testuser')
        UserDetail.objects.create(user=self.user)


    def test_at_work(self):
        """User must have an 'at work' boolean, whose default is False"""
        atwork = UserDetail.objects.get(user=self.user).atwork
        self.assertFalse(atwork)


class TimingViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.userdetail = UserDetail.objects.create(user=self.user)
        self.client.login(username='testuser', password='senha123')

    def test_get(self):
        self.response = self.client.get(r('timing_new'))
        self.assertEqual(200, self.response.status_code)
        self.assertTemplateUsed(self.response, 'timing_new_not_post.html')

    def test_valid_checkin(self):
        """Valid checkin: (a) redirects to 'timing'; b) changes userdetail.atwork to True; (c)
        generates a checkin ticket; (d) the ticket is created by the user"""
        self.userdetail.atwork = False
        self.userdetail.save()
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
        self.userdetail.atwork = True
        self.userdetail.save()
        self.response = self.client.post(r('timing_new'))
        self.assertRedirects(self.response, r('timing', 2))

        atwork = UserDetail.objects.get(user=self.user).atwork
        self.assertFalse(atwork)

        checkout_tickets = Timing.objects.filter(user=self.user, checkin=False)
        self.assertEqual(len(checkout_tickets), 1)

        created_by = checkout_tickets[0].created_by
        self.assertEqual(created_by, self.user)

    def test_invalid_checkout(self):
        """Invalid checkout: (a) occurs when the last checkin happened the day before; b) redirects
        to 'timing', with an alert message; (c) changes userdetail.atwork to False; (d) doesn't
        generate a checkout ticket"""
        activate_timezone()
        d = datetime.datetime.now() + datetime.timedelta(days=-1)
        date_time = timezone.make_aware(d)
        Timing.objects.create(user=self.user, date_time=date_time, checkin=True,
                              created_by=self.user)
        self.userdetail.atwork = True
        self.userdetail.save()
        self.response = self.client.post(r('timing_new'))
        self.assertRedirects(self.response, r('timing_fail'))

        atwork = UserDetail.objects.get(user=self.user).atwork
        self.assertFalse(atwork)


class ForgottenCheckoutsViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user.first_name = 'ze mane'
        self.user.save()

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
        cls.userdetail = UserDetail.objects.create(user=cls.user)

    def setUp(self):
        self.client.login(username='testuser', password='senha123')

    def test_create(self):
        t = Timing.objects.create(
            user=self.user,
            date_time='2016-08-02 11:45:01.017787+00:00') # 'checkin' defaults to 'False'
        self.assertTrue(Timing.objects.exists())

        default_values = (t.checkin, t.created_by)
        self.assertTupleEqual((True, None), default_values)

class RestdayModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.date = Restday.objects.create(
            date=datetime.date(2016, 8, 4),
            note='Jogos olímpicos'
        )

    def test_create(self):
        self.assertTrue(Restday.objects.exists())


class RestdayFormTest(TestCase):

    def test_form_has_fields(self):
        """Form must have 2 fields"""
        form = RestdayForm()
        expected = ('date', 'note')
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


class NewRestdayViewTest(TestCase):

    def setUp(self):
        self.response = self.client.get(r('restday_new'))

    def test_get(self):
        self.assertEqual(200, self.response.status_code)

    def test_template(self):
        self.assertTemplateUsed(self.response, 'newrestday.html')


def activate_timezone():
        return timezone.activate(pytz.timezone('America/Sao_Paulo'))