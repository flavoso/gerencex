# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-26 22:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20161019_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='office',
            name='last_balance_date',
            field=models.DateField(blank=True, null=True, verbose_name='data do último balanço'),
        ),
    ]
