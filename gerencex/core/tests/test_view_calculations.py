import datetime

import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.shortcuts import resolve_url as r
from gerencex.core.models import Timing, Restday, Absences, Office
from gerencex.core.time_calculations import DateData


class CalculationsViewTest(TestCase):

    def setUp(self):
        self.date = datetime.date(2016, 9, 1)
        Office.objects.create(name='Nenhuma lotação',
                              initials='NL',
                              hours_control_start_date=self.date,
                              min_work_hours_for_credit=False
                              )

        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user = User.objects.get(username='testuser')
        self.client.login(username='testuser', password='senha123')
        self.resp = self.client.get(r('calculations',
                                      self.user.username,
                                      self.date.year,
                                      self.date.month,
                                      self.date.day))

    def test_get(self):
        self.assertEqual(200, self.resp.status_code)


def activate_timezone():
    return timezone.activate(pytz.timezone('America/Sao_Paulo'))
