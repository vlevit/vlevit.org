# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('language', models.CharField(max_length=5)),
                ('description', models.CharField(max_length=200, blank=True)),
                ('template', models.CharField(max_length=50)),
                ('list_template', models.CharField(max_length=50)),
                ('export_gplus', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=255)),
                ('digest', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(max_length=100)),
                ('title', models.CharField(max_length=200, blank=True)),
                ('body', models.TextField()),
                ('language', models.CharField(max_length=5)),
                ('template', models.CharField(max_length=50)),
                ('file', models.ForeignKey(to='vlblog.File')),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(max_length=100)),
                ('created', models.DateTimeField()),
                ('title', models.CharField(max_length=200, blank=True)),
                ('body', models.TextField()),
                ('excerpt', models.TextField(blank=True)),
                ('blog', models.ForeignKey(to='vlblog.Blog')),
                ('file', models.ForeignKey(to='vlblog.File')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('n_posts', models.IntegerField(default=0)),
                ('blog', models.ForeignKey(to='vlblog.Blog')),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(to='vlblog.Tag'),
        ),
        migrations.AlterUniqueTogether(
            name='blog',
            unique_together=set([('name', 'language')]),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('name', 'blog')]),
        ),
        migrations.AlterUniqueTogether(
            name='post',
            unique_together=set([('blog', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('name', 'language')]),
        ),
    ]
