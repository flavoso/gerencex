from django.test import TestCase
from django.shortcuts import resolve_url as r
from django.contrib.auth.models import User
from gerencex.core.models import UserDetail


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

class Timesheet(TestCase):

    def setUp(self):
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user = User.objects.get(username='testuser')
        UserDetail.objects.create(user=self.user)
        self.client.login(username='testuser', password='senha123')
        self.response = self.client.get(r('regtime'), follow=True)

    def test_get(self):
        """GET must return status code 200"""
        self.assertEqual(200, self.response.status_code)

    def test_timesheet_change(self):
        """The 'registra-ponto' URL changes the worker's status ('at work' or 'out of work')"""
        self.assertEqual(True, self.user.userdetail.atwork)
