from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Create your models here.

class UserDetail(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                primary_key=True
                                )
    atwork = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Timing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_time = models.DateTimeField(default=timezone.now)
    checkin = models.BooleanField(default=True)

    def __str__(self):
        if self.checkin:
            reg = '{}: {} (Entrada)'.format(self.user, self.date_time)
        else:
            reg = '{}: {} (Saída)'.format(self.user, self.date_time)
        return reg
