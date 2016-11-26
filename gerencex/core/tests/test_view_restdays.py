import datetime

from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.models import Restday


class RestdayTest(TestCase):

    def setUp(self):
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.client.login(username='testuser', password='senha123')
        self.year = timezone.now().year
        Restday.objects.create(
            date=datetime.date(self.year, 11, 15),
            note='Proclamação da República',
        )
        self.resp = self.client.get(r('restdays', self.year))

    def test_get(self):
        """GET must return status code 200"""
        self.assertEqual(200, self.resp.status_code)

    def test_template(self):
        """Must use restdays.html"""
        self.assertTemplateUsed(self.resp, 'restdays.html')

    def test_html(self):
        # print(self.resp.content)
        contents = [
            '15/11/',
            'Proclamação da República',
            '0:00:00'
        ]
        for expected in contents:
            with self.subTest():
                self.assertContains(self.resp, expected)
