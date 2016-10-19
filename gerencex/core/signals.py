from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from gerencex.core.models import HoursBalance, UserDetail, Timing
from gerencex.core.time_calculations import calculate_credit


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


@receiver(post_save, sender=User)
def create_user_userdetail(sender, instance, created, **kwargs):
    if created:
        UserDetail.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_userdetail(sender, instance, **kwargs):
    instance.userdetail.save()


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
            change_balance(date, instance.user, credit)
    else:
        credit = calculate_credit(instance.user, date).seconds
        change_balance(date, instance.user, credit)


def change_balance(date, user, credit):
    balance_line = HoursBalance.objects.filter(date=date, user=user).first()
    if balance_line:
        balance_line.credit = credit
        balance_line.save()
    else:
        HoursBalance.objects.create(
            date=date,
            user=user,
            credit=credit,
            debit=0
        )
