import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from gerencex.core.models import Absences


class AbsencesModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('testuser', 'test@user.com', 'senha123')

    def test_create(self):
        Absences.objects.create(
            date=datetime.date(2016, 9, 5),
            user=self.user,
            cause='curso',
            credit=25200,
            debit=0
        )

        self.assertTrue(Absences.objects.exists())
