from django.db import models


class Blog(models.Model):

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.name


class Tag(models.Model):

    name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.name


class Post(models.Model):

    blog = models.ForeignKey(Blog)
    created = models.DateTimeField()
    title = models.CharField(max_length=200, blank=True)
    tags = models.ManyToManyField(Tag)
    body = models.TextField()
    excerpt = models.TextField(blank=True)

    def __unicode__(self):
        return self.title
