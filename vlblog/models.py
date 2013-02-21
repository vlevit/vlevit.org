from django.db import models


class Blog(models.Model):

    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.name


class Tag(models.Model):

    name = models.CharField(max_length=50, unique=True)
    blog = models.ForeignKey(Blog)
    language = models.CharField(max_length=5)
    n_posts = models.IntegerField(default=0,
                                  help_text="Number of posts with this tag "
                                  "of the same blog and the same language")

    def __unicode__(self):
        return self.name


class Post(models.Model):

    blog = models.ForeignKey(Blog)
    language = models.CharField(max_length=5)
    post_id = models.CharField(
        max_length=200, blank=True,
        help_text="Used to link posts of different languages")
    created = models.DateTimeField()
    tags = models.ManyToManyField(Tag, null=True)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    excerpt = models.TextField(blank=True)

    def __unicode__(self):
        return self.title
