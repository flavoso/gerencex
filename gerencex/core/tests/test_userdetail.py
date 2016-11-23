from django.contrib.auth.models import User
from django.test import TestCase
from gerencex.core.models import Office


class UserDetailTest(TestCase):

    def setUp(self):
        Office.objects.create(name='Nenhuma lotação',
                              initials='NL')
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user = User.objects.get(username='testuser')
        # UserDetail.objects.create(user=self.user)

    def test_userdetail_create(self):
        """
        User must have default values for 'atwork' (False) and office ('Nenhuma lotação')
        """
        atwork = self.user.userdetail.atwork
        office = self.user.userdetail.office.initials
        self.assertFalse(atwork)
        self.assertEqual('NL', office)

    def test_userdetail_save(self):
        """
        User must have default values for 'atwork' (False) and office ('Nenhuma lotação')
        """
        user2 = User(username='testuser2',
                     email='test2@user.com',
                     password='senha321')
        user2.save()
        atwork = user2.userdetail.atwork
        office = user2.userdetail.office.initials
        self.assertFalse(atwork)
        self.assertEqual('NL', office)

