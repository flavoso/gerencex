from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase


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
