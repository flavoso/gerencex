import datetime

from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.models import Restday, Office


class OfficeTicketsViewTest(TestCase):

    def setUp(self):
        self.office = Office.objects.create(
            name='Terceira Diacomp',
            initials='DIACOMP3'
        )
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user = User.objects.get(username='testuser')
        self.user.first_name = 'Ze'
        self.user.last_name = 'Mane'
        self.user.userdetail.office = self.office
        self.user.save()
        self.client.login(username='testuser', password='senha123')
        self.resp = self.client.get(r('office_tickets'))

    def test_get(self):
        """GET must return status code 200"""
        self.assertEqual(200, self.resp.status_code)

    def test_template(self):
        """Must use restdays.html"""
        self.assertTemplateUsed(self.resp, 'office_tickets.html')

    def test_html(self):
        # print(self.resp.content)
        contents = [
            'Terceira Diacomp',
            'Ze Mane'
        ]
        for expected in contents:
            with self.subTest():
                self.assertContains(self.resp, expected)
