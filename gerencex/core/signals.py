from datetime import timedelta

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from gerencex.core.models import HoursBalance


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
