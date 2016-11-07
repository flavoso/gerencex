from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.utils import timezone
from django.dispatch import receiver
from gerencex.core.models import HoursBalance, UserDetail, Timing, Restday, Absences, Office
from gerencex.core.time_calculations import calculate_credit, calculate_debit


@receiver(pre_save, sender=HoursBalance)
def total_balance_handler(sender, instance, **kwargs):
    """
    Before saving, the daily balance must be calculated, taking into account the previous balance
    and the daily credit and debit.
    """
    previous = sender.objects.filter(user=instance.user, date__lt=instance.date).last()
    if previous is not None:
        instance.balance = previous.balance + instance.credit - instance.debit
    else:
        instance.balance = instance.credit - instance.debit


@receiver(post_save, sender=HoursBalance)
def next_balance_handler(sender, instance, created, **kwargs):
    """
    After saving, the next balance must be recalculated, if it exists.
    """
    if not created:
        next_bal = sender.objects.filter(user=instance.user, date__gt=instance.date).first()
        if next_bal and next_bal.pk != instance.pk:
            next_bal.save()


@receiver(pre_save, sender=User)
def create_default_office(sender, instance, **kwargs):
    if not Office.objects.filter(pk=1):
        Office.objects.create(
            name='nenhuma lotação',
            initials='NL'
        )


@receiver(post_save, sender=User)
def create_user_userdetail(sender, instance, created, **kwargs):
    if created:
        UserDetail.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_userdetail(sender, instance, **kwargs):

    # The following condition avoids error when trying to save a User which does not have
    # UserDetail (for example, the admin user, created at project's beginning).

    if UserDetail.objects.filter(user=instance):
        instance.userdetail.save()
    else:
        UserDetail.objects.create(user=instance)


@receiver(post_save, sender=Timing)
def credit_calculation(sender, instance, created, **kwargs):
    date = instance.date_time.date()

    if instance.checkin:
        next_ticket_is_checkout = sender.objects.filter(user=instance.user,
                                                        date_time__date=date,
                                                        date_time__gt=instance.date_time,
                                                        checkin=False).first()
        if next_ticket_is_checkout:
            credit = calculate_credit(instance.user, date).seconds
            debit = calculate_debit(instance.user, date).seconds
            change_balance(date, instance.user, credit, debit)
    else:
        credit = calculate_credit(instance.user, date).seconds
        debit = calculate_debit(instance.user, date).seconds
        change_balance(date, instance.user, credit, debit)


@receiver(post_save, sender=Restday)
def debit_calculation_restday(sender, instance, created, **kwargs):
    """
    When a we record a Restday whose date is already in lines at HoursBalance, we must
    recalculate the balance at these lines.
    """
    balance_lines = [x for x in HoursBalance.objects.filter(date=instance.date,
                                                            user__is_superuser=False)]
    if len(balance_lines) != 0:
        for line in balance_lines:
            line.debit = calculate_debit(line.user, instance.date).seconds
            line.save()


@receiver(post_save, sender=Absences)
def debit_calculation_absence(sender, instance, created, **kwargs):
    """
    When an Absence debit registry is changed, it must be recalculated the daily balance for the
    date of that registry, if it exists.
    """

    if instance.debit != 0:
        balance_line = HoursBalance.objects.filter(date=instance.date,
                                                   user=instance.user)
        if balance_line:
            balance_line = calculate_debit(instance.user, instance.date).seconds
            balance_line.save()


def change_balance(date, user, credit, debit):
    updated_values = {
        'credit': credit,
        'debit': debit
    }
    HoursBalance.objects.update_or_create(
        date=date,
        user=user,
        defaults=updated_values
    )

    # balance_line = HoursBalance.objects.filter(date=date, user=user).first()
    # if balance_line:
    #     balance_line.credit = credit
    #     balance_line.debit = debit
    #     balance_line.save()
    # else:
    #     HoursBalance.objects.create(
    #         date=date,
    #         user=user,
    #         credit=credit,
    #         debit=debit
    #     )