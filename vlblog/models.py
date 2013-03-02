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
    # number of posts with this tag of the same blog and the same language
    n_posts = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

    @classmethod
    def new_tag(cls, tagname, blog, language):
        try:
            tag = cls.objects.get(name=tagname, blog=blog, language=language)
        except cls.DoesNotExist:
            tag = cls(name=tagname, blog=blog, language=language)
        tag.n_posts += 1
        tag.save()
        return tag


class Post(models.Model):

    # relative path to the source starting from CONTENT_DIR
    file = models.CharField(max_length=256)
    file_digest = models.CharField(max_length=20)
    blog = models.ForeignKey(Blog)
    language = models.CharField(max_length=5)
    # unique name per blog per language, the part of url
    # also used to link posts of different languages
    name = models.SlugField(max_length=50)
    created = models.DateTimeField()
    tags = models.ManyToManyField(Tag, null=True)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    excerpt = models.TextField(blank=True)

    class Meta:
        unique_together = (('blog', 'language', 'name'))
        ordering = ['-created']

    def __unicode__(self):
        return "{}: {}: {}".format(self.blog.name, self.language, self.name)

    def clear_tags(self):
        for tag in self.tags.all():
            if tag.n_posts <= 1:
                tag.delete()
            else:
                tag.n_posts -= 1
                tag.save()
        self.tags.clear()
