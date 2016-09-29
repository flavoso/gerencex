from datetime import timedelta

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
                            unique=True)
    note = models.CharField('descrição', max_length=50)
    work_hours = models.DurationField('carga horária', default=timedelta(hours=0))

    class Meta:
        verbose_name_plural = 'dias não úteis'
        verbose_name = 'dia não útil'
        ordering = ['date']

    def __str__(self):
        return '{}: {} ({}) horas'.format(self.date, self.note, self.work_hours)


class HoursBalance(models.Model):

    date = models.DateField('data',)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='hours')
    credit = models.IntegerField('crédito')
    debit = models.IntegerField('débito')
    balance = models.IntegerField('saldo acumulado')

    class Meta:
        verbose_name = 'banco de horas'
        verbose_name_plural = 'banco de horas'
        ordering = ['date', 'user']
        unique_together = ('date', 'user')
        index_together = ['date', 'user']
        get_latest_by = 'date'

    def time_credit(self):
        return str(timedelta(seconds=self.credit))

    def time_debit(self):
        return str(timedelta(seconds=self.debit))

    def time_balance(self):
        if self.balance < 0:
            return '-{}'.format(timedelta(seconds=abs(self.balance)))
        return str(timedelta(self.balance))

    time_credit.short_description = 'crédito'
    time_debit.short_description = 'débito'
    time_balance.short_description = 'saldo'

    def __str__(self):
        return '{} -- {} : {}'.format(self.date, self.user, str(self.balance))


class Absences(models.Model):

    CURSO = 'CR'
    CEDIDO = 'CD'
    INSPECAO = 'IN'
    FERIAS = 'FR'
    LIC_MEDICA = 'LM'
    LIC_PREMIO = 'LP'
    LIC_POLIT = 'LA'
    GOZO_RECESSO = 'GR'
    OUTROS = 'OU'

    ABSENCES_CHOICES = (
        (CURSO, 'Curso'),
        (CEDIDO, 'Cedido para outra unidade'),
        (INSPECAO, 'Inspeção'),
        (FERIAS, 'Férias (formal)'),
        (LIC_MEDICA, 'Licença médica'),
        (LIC_PREMIO, 'Licença-prêmio'),
        (LIC_POLIT, 'Licença para atividade política'),
        (GOZO_RECESSO, 'Gozo do recesso (formal)'),
        (OUTROS, 'Outros afastamentos'),
    )

    date = models.DateField('data',)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='absences')
    cause = models.CharField('motivo', max_length=2, choices=ABSENCES_CHOICES, default=FERIAS)
    credit = models.IntegerField('crédito', default=0)
    debit = models.IntegerField('débito', default=0)

    class Meta:
        verbose_name = 'Afastamento'
        verbose_name_plural = 'Afastamentos'
        ordering = ['user', '-date']
        unique_together = ('date', 'user')
        index_together = ['date', 'user']
        get_latest_by = 'date'

    def __str__(self):
        return '{} -- {} : {}'.format(self.date, self.user, self.cause)