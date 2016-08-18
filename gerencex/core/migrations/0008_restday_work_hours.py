# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-15 12:59
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20160813_2316'),
    ]

    operations = [
        migrations.AddField(
            model_name='restday',
            name='work_hours',
            field=models.DurationField(default=datetime.timedelta(0), verbose_name='carga horária'),
        ),
    ]
