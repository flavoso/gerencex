from datetime import timedelta

from django.db.models.signals import pre_save
from django.dispatch import receiver
from gerencex.core.models import HoursBalance


@receiver(pre_save, sender=HoursBalance)
def total_balance_handler(sender, instance, **kwargs):
    previous = sender.objects.filter(user=instance.user).last()
    if previous is not None:
        instance.balance = previous.balance + instance.credit - instance.debit
    else:
        instance.balance = instance.credit - instance.debit
