from datetime import timedelta, time

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from gerencex.core.validators import validate_date


# Create your models here.

class UserDetail(models.Model):
    """
    The default values are set at User's creation or saving (via signals). See 'signals.py'
    """
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                primary_key=True
                                )
    atwork = models.BooleanField(default=False)
    office = models.ForeignKey('Office',
                               models.SET_DEFAULT,
                               default=1,
                               null=True,
                               blank=True,
                               related_name='users'
                               )
    opening_hours_balance = models.IntegerField('saldo inicial',
                                                default=0)

    def __str__(self):
        return self.user.username


class Timing(models.Model):
    user = models.ForeignKey(User,
                             models.CASCADE,
                             related_name='tickets')
    date_time = models.DateTimeField(default=timezone.now)
    checkin = models.BooleanField(default=True)
    created_by = models.ForeignKey(User,
                                   models.SET_NULL,
                                   null=True,
                                   blank=True)
    client_ip = models.CharField('ip do cliente',
                                 max_length=15,
                                 blank=True,
                                 default='')
    client_local_ip = models.CharField('ip local do cliente',
                                       max_length=15,
                                       blank=True,
                                       default='')

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
    """
    The user balance is always calculated via signals. See 'signals.py'
    """

    date = models.DateField('data',)
    user = models.ForeignKey(User,
                             models.CASCADE,
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
        return str(timedelta(seconds=self.balance))

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
    FALTA = 'FT'
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
        (FALTA, 'Falta não justificada'),
        (OUTROS, 'Outros afastamentos'),
    )

    date = models.DateField('data',)
    user = models.ForeignKey(User,
                             models.CASCADE,
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


class Office(models.Model):
    """
    'TCU' stands for Tribunal de Contas da União, the brazilian federal court for account
    settlement, similar to U.S. Government Accountability Office (U.S. GAO)
    """
    name = models.CharField('nome', max_length=100)
    initials = models.CharField('sigla', max_length=15)
    active = models.BooleanField('unidade ativa', default=True)
    regular_work_hours = models.DurationField('jornada diária',
                                              default=timedelta(hours=7))           # TCU: 7 hours
    max_daily_credit = models.BooleanField('restrição de jornada diária máxima',
                                                default=False)
    max_daily_credit_value = models.DurationField('restrição de valor da máxima jornada diária',
                                                  default=timedelta(hours=10))      # TCU: 10 hours
    max_monthly_balance = models.BooleanField('restrição de saldo mensal máximo de horas',
                                              default=False)
    max_monthly_balance_value = models.DurationField('valor do saldo mensal máximo',
                                                     default=timedelta(hours=20))   # TCU: 20 hours
    min_checkin_time = models.BooleanField('restrição de horário mínimo para entrada',
                                           default=False)
    min_checkin_time_value = models.TimeField('horário mínimo para entrada',
                                              default=time(8, 0, 0))                # TCU: 08h00
    max_checkout_time = models.BooleanField('restrição de horário máximo para saída',
                                            default=False)
    max_checkout_time_value = models.TimeField('horário máximo para saída',
                                               default=time(20, 0, 0))              # TCU: 20h00
    checkin_tolerance = models.DurationField('tolerância para entrada',
                                             default=timedelta(minutes=10))
    checkout_tolerance = models.DurationField('tolerância para saída',
                                              default=timedelta(minutes=5))
    hours_control_start_date = models.DateField('data de início do controle de horas',
                                                null=True,
                                                blank=True)
    last_balance_date = models.DateField('data do último balanço',
                                         null=True,
                                         blank=True)
    min_work_hours_for_credit = models.BooleanField(
        'restrição de jornada diária necessária para acumular créditos',
        default=True)
    min_work_hours_for_credit_value = models.DurationField(
        'jornada diária necessária para acumular créditos',
        default=timedelta(hours=7))
    linked_to = models.ForeignKey('self',
                                  models.SET_DEFAULT,
                                  default=1,
                                  blank=True,
                                  null=True,
                                  related_name='linkedin')

    class Meta:
        verbose_name = 'Lotação'
        verbose_name_plural = 'Lotações'
        ordering = ['initials']

    def __str__(self):
        return '{}'.format(self.initials)