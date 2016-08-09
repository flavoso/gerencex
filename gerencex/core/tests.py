import datetime

from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
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

        self.assertEqual(False, self.user.userdetail.atwork)


# class TimingViewTest(TestCase):
#
#     def setUp(self):
#         self.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
#         self.userdetail = UserDetail.objects.create(user=self.user)
#         self.client.login(username='testuser', password='senha123')
#         self.response = self.client.post(r('timing_new'), {})
#
#     def test_timing_new_post_redirect(self):
#         """POST redirects to 'timing'."""
#         self.assertRedirects(self.response, r('timing', 1))
#
#     def test_timing_new_post_changes_atwork(self):
#         """POST changes 'userdetail.atwork'."""
#         self.userdetail.refresh_from_db()
#         self.assertTrue(self.userdetail.atwork)


    # def test_timing_get(self):
    #
    #     self.response = self.client.get(r('timing'))
    #     self.assertEqual(200, self.response.status_code)
    # #     # TODO: talvez isso só possa ser testado com Teste Funcional
    # #     qs = UserDetail.objects.get(user=self.user)
    # #     self.assertTrue(qs.atwork)
    #
    # def test_timing_template(self):
    #     """The 'timing.html' template should be used."""
    #     self.response = self.client.get(r('timing'))
    #     self.assertTemplateUsed(self.response, 'timing.html')

    # def test_checkout_error(self):
    #     """Check outs are not valid if there was not a previous check in in the same day"""
    #     Timing.objects.create(user=self.user,
    #                           date_time=datetime.datetime(year=2016, month=8, day=5, hour=13),
    #                           checkin=True)
    #     self.response = self.client.post(r('timing'), {})
    #     self.assertEqual(self.response.context['register'], 'falha')


class TimingModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
        cls.userdetail = UserDetail.objects.create(user=cls.user)

    def setUp(self):
        self.client.login(username='testuser', password='senha123')

    def test_create(self):
        timing = Timing.objects.create(
            user=self.user,
            date_time='2016-08-02 11:45:01.017787+00:00',
            checkin=False)
        self.assertTrue(Timing.objects.exists())


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

    # def assertFormErrorMessage(self, form, field, msg):
    #     errors = form.errors
    #     error_list = errors[field]
    #     self.assertListEqual([msg], error_list)

class NewRestdayViewTest(TestCase):

    def setUp(self):
        self.response = self.client.get(r('newrestday'))

    def test_get(self):
        self.assertEqual(200, self.response.status_code)

    def test_template(self):
        self.assertTemplateUsed(self.response, 'newrestday.html')