from django.db import models


class Blog(models.Model):

    name = models.CharField(max_length=50, unique=True)
    language = models.CharField(max_length=5)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = (('name', 'language'))

    def __unicode__(self):
        return "{}: {}".format(self.language, self.name)

    @classmethod
    def get_or_create(cls, name, language, description):
        """
        Return an existing Blog object with specified name and language.
        If specified and existing descriptions differ, update the field to new
        description.

        If blog with specified language and description doesn't exist,
        create and return a new blog.

        """
        try:
            blog = Blog.objects.get(name=name, language=language)
        except Blog.DoesNotExist:
            blog = Blog(name=name, language=language, description=description)
            blog.save()
        else:
            if blog.description != description:
                blog.description = description
                blog.save()
        return blog


class Tag(models.Model):

    name = models.CharField(max_length=50, unique=True)
    blog = models.ForeignKey(Blog)
    # number of posts with this tag of the same blog
    n_posts = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

    @classmethod
    def get_or_create(cls, tagname, blog):
        """
        Return an existing Tag object with specified tag name and blog,
        or if doesn't exist, create a new one and return it.

        """
        try:
            tag = cls.objects.get(name=tagname, blog=blog)
        except cls.DoesNotExist:
            tag = cls(name=tagname, blog=blog)
        tag.n_posts += 1
        tag.save()
        return tag


class Post(models.Model):

    # relative path to the source starting from CONTENT_DIR
    file = models.CharField(max_length=256)
    file_digest = models.CharField(max_length=40)
    blog = models.ForeignKey(Blog)
    # unique name per blog, the part of url
    # also used to link posts of different languages
    name = models.SlugField(max_length=50)
    created = models.DateTimeField()
    tags = models.ManyToManyField(Tag, null=True)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    excerpt = models.TextField(blank=True)

    class Meta:
        unique_together = (('blog', 'name'))
        ordering = ['-created']

    def __unicode__(self):
        return "{}: {}".format(self.blog, self.name)

    @classmethod
    def insert_or_update(cls, data, blog, pk=None):
        """
        If pk is None, create a new post from data and save.
        If pk is not None, update that post with data and save.

        data['tags'] is expected to be a list of strings, not objects

        """
        data['blog'] = blog
        tagnames = data.pop('tags')
        tags = []
        # post update: clear old posts' tags
        if pk is not None:
            post = Post.objects.get(pk=pk)
            post.clear_tags()
        for tagname in tagnames:
            tag = Tag.get_or_create(tagname, blog)
            tag.save()
            tags.append(tag)
        post = Post(**data)
        post.pk = pk
        post.save()
        post.tags.add(*tags)

    @classmethod
    def rename(cls, pk, new_file, new_name=None):
        """
        Change Post's file field to a new_file.
        If new_name is specified, change Post's name too.

        """
        post = cls.objects.get(pk=pk)
        post.file = new_file
        if new_name:
            post.name = new_name
        post.save()

    @classmethod
    def delete(cls, pk):
        """
        Delete post by primary key.

        """
        cls.objects.get(pk=pk).delete()

    def clear_tags(self):
        """
        Consistently remove all tags from the post.

        """
        for tag in self.tags.all():
            if tag.n_posts <= 1:
                tag.delete()
            else:
                tag.n_posts -= 1
                tag.save()
        self.tags.clear()
