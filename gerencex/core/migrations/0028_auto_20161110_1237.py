# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-10 12:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_remove_hoursbalance_adjusted_balance'),
    ]

    operations = [
        migrations.RenameField(
            model_name='office',
            old_name='min_work_hours_for_credit',
            new_name='min_work_hours_for_credit_value',
        ),
    ]