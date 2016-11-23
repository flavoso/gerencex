import datetime

import pytz
from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.models import Timing, Office


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


def activate_timezone():
    return timezone.activate(pytz.timezone('America/Sao_Paulo'))
