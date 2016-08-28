# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-28 22:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20160827_0116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hoursbalance',
            name='balance',
            field=models.IntegerField(verbose_name='saldo acumulado'),
        ),
        migrations.AlterField(
            model_name='hoursbalance',
            name='credit',
            field=models.IntegerField(verbose_name='crédito'),
        ),
        migrations.AlterField(
            model_name='hoursbalance',
            name='debit',
            field=models.IntegerField(default=25200, verbose_name='débito'),
        ),
    ]
