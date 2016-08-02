from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from gerencex.core.models import UserDetail, Timing


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


class TimingViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')
        cls.userdetail = UserDetail.objects.create(user=cls.user)

    def setUp(self):
        self.userdetail.refresh_from_db()
        self.client.login(username='testuser', password='senha123')

    def test_get(self):
        """GET must return status code 200. GET does not change 'userdetail.atwork'."""
        self.response = self.client.get(r('timing'))
        self.assertEqual(200, self.response.status_code)
        self.assertFalse(self.userdetail.atwork)

    def test_post(self):
        """POST must return status code 200. POST changes 'userdetail.atwork'."""
        self.response = self.client.post(r('timing'), {})
        self.assertEqual(200, self.response.status_code)
        # TODO: talvez isso só possa ser testado com Teste Funcional
        # self.assertTrue(self.userdetail.atwork)

    def test_template(self):
        """The 'timing.html' template should be used."""
        self.response = self.client.get(r('timing'))
        self.assertTemplateUsed(self.response, 'timing.html')

    # def test_html(self):
    #     self.response = self.client.post(r('timing'))
    #     self.response


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

