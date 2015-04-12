# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('sensor_name', models.CharField(max_length=255, serialize=False, primary_key=True, db_index=True)),
                ('channel', models.CharField(max_length=256, db_index=True)),
                ('time', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
