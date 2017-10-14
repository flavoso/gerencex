from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase
from django.shortcuts import resolve_url as r
from gerencex.core.models import Office


class ManualCheckView(TestCase):

    def setUp(self):
        self.office = Office.objects.create(
            name='Terceira Diacomp',
            initials='DIACOMP3'
        )

        # Creating user that belongs to 'managers' group
        User.objects.create_user('testuser', 'test@user.com', 'senha123')
        self.user = User.objects.get(username='testuser')
        self.user.first_name = 'Ze'
        self.user.last_name = 'Mane'
        self.user.userdetail.office = self.office
        self.user.save()
        add_user_to_managers_group(self.user)

        # Creating user that doesn't belong to 'managers' group
        User.objects.create_user('testuser2', 'test2@user.com', 'senha123')
        self.user2 = User.objects.get(username='testuser2')
        self.user2.first_name = 'Ze'
        self.user2.last_name = 'Ruela'
        self.user2.userdetail.office = self.office
        self.user.save()

    def test_get_manager(self):
        self.client.login(username='testuser', password='senha123')
        self.resp = self.client.get(r('manual_check'))
        self.assertEquals(200, self.resp.status_code)

    def test_get_not_manager(self):
        self.client.login(username='testuser2', password='senha123')
        self.resp2 = self.client.get(r('manual_check'))
        self.assertEqual(302, self.resp2.status_code)


def add_user_to_managers_group(user):
    Group.objects.create(name='managers')
    group = Group.objects.get(name='managers')
    perm1 = Permission.objects.get(codename='add_timing')
    perm2 = Permission.objects.get(codename='change_timing')
    perm3 = Permission.objects.get(codename='delete_timing')
    group.permissions.add(perm1, perm2, perm3)
    user.groups.add(group)
