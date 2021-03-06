# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-08 19:37
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_office_min_work_hours_for_credit'),
    ]

    operations = [
        migrations.AddField(
            model_name='hoursbalance',
            name='adjusted_balance',
            field=models.IntegerField(default=0, verbose_name='saldo acumulado ajustado'),
        ),
        migrations.AlterField(
            model_name='office',
            name='hours_control_start_date',
            field=models.DateField(blank=True, null=True, verbose_name='data de início do controle de horas'),
        ),
        migrations.AlterField(
            model_name='office',
            name='min_work_hours_for_credit',
            field=models.DurationField(default=datetime.timedelta(0, 25200), verbose_name='jornada diária necessária para acumular créditos'),
        ),
    ]
