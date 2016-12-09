# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-07 20:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_office_min_work_hours_for_credit'),
    ]

    operations = [
        migrations.AddField(
            model_name='office',
            name='linked_to',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='subordinates', to='core.Office'),
        ),
    ]