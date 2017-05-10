import datetime

import pytz
from django.contrib.auth.models import User
from django.shortcuts import resolve_url as r
from django.test import TestCase
from django.utils import timezone
from gerencex.core.models import UserDetail, Timing, Office


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
        utc_offset = datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).utcoffset()
        now = datetime.datetime.now() + utc_offset
        d = now + datetime.timedelta(hours=-1)
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
        before; b) redirects to 'timing_fail'; (c) changes userdetail.atwork to False;
        (d) doesn't generate a checkout ticket"""
        activate_timezone()
        utc_offset = datetime.datetime.now(pytz.timezone('America/Sao_Paulo')).utcoffset()
        now = datetime.datetime.now() + utc_offset
        d = now + datetime.timedelta(days=-1)
        date_time = timezone.make_aware(d)
        Timing.objects.create(user=self.user, date_time=date_time, checkin=True,
                              created_by=self.user)
        self.user.userdetail.atwork = True
        self.user.save()
        self.response = self.client.post(r('timing_new'))
        self.assertRedirects(self.response, r('timing_fail'))

        atwork = UserDetail.objects.get(user=self.user).atwork
        self.assertFalse(atwork)

        checked_in = bool(Timing.objects.filter(date_time__date=now.date()))
        self.assertFalse(checked_in)


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


def activate_timezone():
    return timezone.activate(pytz.timezone('America/Sao_Paulo'))


