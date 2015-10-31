from django.core.urlresolvers import reverse
from django.db import models
from django.utils import translation


class Blog(models.Model):

    name = models.CharField(max_length=50)
    language = models.CharField(max_length=5)
    description = models.CharField(max_length=200, blank=True)
    template = models.CharField(max_length=50)
    list_template = models.CharField(max_length=50)
    export_gplus = models.BooleanField()
    per_page = models.IntegerField(default=1024)

    class Meta:
        unique_together = ('name', 'language')

    def __unicode__(self):
        return "{}: {}".format(self.language, self.name)

    def get_absolute_url(self):
        with translation.override(self.language):
            permalink = reverse('post_list', args=(self.name,))
        return permalink

    @classmethod
    def get_or_create(cls, **kwargs):
        """
        Return an existing Blog object with specified name and language.

        If some specified arguments and existing fields differ, update fields
        to new specified values.

        If blog with specified name and language doesn't exist, create and
        return a new blog.

        """
        save = False
        try:
            blog = Blog.objects.get(name=kwargs['name'],
                                    language=kwargs['language'])
        except Blog.DoesNotExist:
            blog = Blog(**kwargs)
            save = True
        else:
            for fname in blog._meta.get_all_field_names():
                if fname in kwargs and getattr(blog, fname) != kwargs[fname]:
                    setattr(blog, fname, kwargs[fname])
                    save = True
        if save:
            blog.save()
        return blog


class Tag(models.Model):

    name = models.CharField(max_length=100)
    blog = models.ForeignKey(Blog)
    # number of posts with this tag of the same blog
    n_posts = models.IntegerField(default=0)

    class Meta:
        unique_together = ('name', 'blog')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        with translation.override(self.blog.language):
            permalink = reverse('post_list_tag',
                                args=(self.blog.name, self.name))
        return permalink

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


class File(models.Model):
    # absolute path to file
    path = models.CharField(max_length=255, unique=True)
    digest = models.CharField(max_length=40)

    def __unicode__(self):
        return self.path


class Post(models.Model):

    file = models.ForeignKey(File)
    blog = models.ForeignKey(Blog)
    # unique name per blog, the part of url
    # also used to link posts of different languages
    name = models.SlugField(max_length=100)
    created = models.DateTimeField()
    published = models.DateTimeField(null=True)
    tags = models.ManyToManyField(Tag)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    excerpt = models.TextField(blank=True)

    class Meta:
        unique_together = ('blog', 'name')
        ordering = ['-created']

    def __unicode__(self):
        return "{}: {}".format(self.blog, self.name)

    def get_absolute_url(self):
        with translation.override(self.blog.language):
            permalink = reverse('post', args=(self.blog.name, self.name))
        return permalink

    @classmethod
    def insert_or_update(cls, data, file, blog):
        """
        Create or update post from data and save it.

        data['tags'] is expected to be a list of strings, not objects

        """
        data['blog'] = blog
        data['file'] = file
        tagnames = data.pop('tags')
        tags = []

        try:
            post = Post.objects.get(blog=blog, name=data['name'])
            pk = post.pk
        except cls.DoesNotExist:
            pk = None
        else:
            post.clear_tags()
        for tagname in tagnames:
            tag = Tag.get_or_create(tagname, blog)
            tag.save()
            tags.append(tag)

        post = Post(**data)
        post.pk = pk
        post.save()
        post.tags.add(*tags)

    def delete(self, *args, **kwargs):
        """
        Delete post cleanly.

        """
        self.clear_tags()
        super(Post, self).delete(*args, **kwargs)

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


class Page(models.Model):

    file = models.ForeignKey(File)
    # unique name per language, the part of url
    name = models.SlugField(max_length=100)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    language = models.CharField(max_length=5)
    template = models.CharField(max_length=50)

    class Meta:
        unique_together = ('name', 'language')

    def __unicode__(self):
        return "{}: {}".format(self.language, self.name)

    def get_absolute_url(self):
        with translation.override(self.language):
            permalink = reverse('page', args=(self.name,))
        return permalink
