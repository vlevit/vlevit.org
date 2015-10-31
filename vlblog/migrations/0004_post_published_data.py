# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_published(apps, schema_editor):
    Post = apps.get_model('vlblog', 'Post')
    Post.objects.update(published=models.F('created'))


class Migration(migrations.Migration):

    dependencies = [
        ('vlblog', '0003_post_published'),
    ]

    operations = [
        migrations.RunPython(populate_published),
    ]
