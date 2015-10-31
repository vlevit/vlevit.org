# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vlblog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='per_page',
            field=models.IntegerField(default=1024),
        ),
    ]
