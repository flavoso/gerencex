from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from gerencex.core.validators import validate_date


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
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='tickets')
    date_time = models.DateTimeField(default=timezone.now)
    checkin = models.BooleanField(default=True)
    created_by = models.ForeignKey(User,
                                   on_delete=models.CASCADE,
                                   null=True)

    class Meta:
        verbose_name_plural = 'registros de entrada e saída'
        verbose_name = 'registro de entrada e saída'
        ordering = ['date_time']

    def __str__(self):
        if self.checkin:
            reg = '{}: {} (Entrada)'.format(self.user, self.date_time)
        else:
            reg = '{}: {} (Saída)'.format(self.user, self.date_time)
        return reg


class Restday(models.Model):

    date = models.DateField('data',
                            validators=[validate_date],
                            help_text='Formato DD/MM/AAAA',
                            unique_for_date=True)
    note = models.CharField('descrição', max_length=50)

    class Meta:
        verbose_name_plural = 'dias não úteis'
        verbose_name = 'dia não útil'
        ordering = ['date']

    def __str__(self):
        return '{}: {}'.format(self.date, self.note)