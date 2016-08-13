# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-05 13:39
from __future__ import unicode_literals

from django.db import migrations, models
import gerencex.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_timing'),
    ]

    operations = [
        migrations.CreateModel(
            name='Restday',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(validators=[gerencex.core.validators.validate_date], verbose_name='data')),
                ('note', models.CharField(max_length=50, verbose_name='descrição')),
            ],
            options={
                'verbose_name_plural': 'dias não úteis',
                'verbose_name': 'dia não útil',
                'ordering': ('date',),
            },
        ),
        migrations.AlterModelOptions(
            name='timing',
            options={'ordering': ('date_time',), 'verbose_name': 'registro', 'verbose_name_plural': 'registros'},
        ),
    ]