import django_comments as comments
from django.contrib.contenttypes.models import ContentType
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from vlblog.models import Blog, Page, Post, Tag


class FeedBase(Feed):

    description_template = 'feeds/post.html'

    def item_title(self, post):
        return post.title

    def item_pubdate(self, post):
        return post.published

    def item_categories(self, post):
        return post.tags.all()

    def author_name(self):      # will not show up in RSS
        return _("Vyacheslav Levit")

    def author_link(self):      # will not show up in RSS
        return "http://vlevit.org/"

    item_author_name = author_name
    item_author_link = author_link  # will not show up in RSS


class SiteFeed(FeedBase):

    def get_object(self, request):
        return request

    def link(self, request):
        return "http://{}/".format(request.get_host())

    def title(self, request):
        return request.get_host()

    description = title

    def items(self, request):
        return Post.objects.filter(
            blog__language=request.LANGUAGE_CODE).prefetch_related('tags')


class BlogFeed(FeedBase):

    def get_object(self, request, blog):
        return get_object_or_404(Blog, name=blog,
                                 language=request.LANGUAGE_CODE)

    def link(self, blog):
        return blog.get_absolute_url()

    def title(self, blog):
        return blog.description

    description = title

    def items(self, blog):
        return Post.objects.filter(blog=blog).prefetch_related('tags')


class TagFeed(FeedBase):

    def get_object(self, request, blog, tag):
        return get_object_or_404(Tag, name__iexact=tag, blog__name=blog,
                                 blog__language=request.LANGUAGE_CODE)

    def link(self, tag):
        return tag.get_absolute_url()

    def title(self, tag):
        return u"{} - {}".format(tag.blog.description, tag.name)

    description = title

    def items(self, tag):
        return Post.objects.filter(tags__pk=tag.pk) \
                           .select_related('blog') \
                           .prefetch_related('tags')


class CommentsFeedBase(Feed):

    description_template = 'feeds/comment.html'

    def item_title(self, comment):
        return _("Comment on \"{}\"").format(comment.content_object.title)

    def item_link(self, comment):
        post = comment.content_object
        url = "{}#c{}".format(post.get_absolute_url(), comment.id)
        return url

    def item_author_name(self, comment):
        return comment.user_name

    def item_author_link(self, comment):  # will not show up in RSS
        return comment.user_url

    def item_pubdate(self, comment):
        return comment.submit_date


class SiteCommentsFeed(CommentsFeedBase):

    def get_object(self, request):
        return request

    def link(self, request):
        return "http://{}/".format(request.get_host())

    def title(self, request):
        return _("Comments on \"{}\"").format(request.get_host())

    description = title

    def items(self, request):
        CommentModel = comments.get_model()
        post_ids = Post.objects.filter(
            blog__language=request.LANGUAGE_CODE).values_list('id', flat=True)
        return (CommentModel.objects.filter(
            is_public=True, is_removed=False,
            content_type=ContentType.objects.get_for_model(Post),
            object_pk__in=map(str, post_ids))
                .order_by('-submit_date')
                .prefetch_related('content_object'))


class BlogCommentsFeed(CommentsFeedBase):

    def get_object(self, request, blog):
        return get_object_or_404(Blog, name=blog,
                                 language=request.LANGUAGE_CODE)

    def link(self, blog):
        return blog.get_absolute_url()

    def title(self, blog):
        return _("Comments on blog \"{}\"").format(blog.description)

    description = title

    def items(self, blog):
        CommentModel = comments.get_model()
        post_ids = Post.objects.filter(blog=blog).values_list('id', flat=True)
        return (CommentModel.objects.filter(
            is_public=True, is_removed=False,
            content_type=ContentType.objects.get_for_model(Post),
            object_pk__in=map(str, post_ids))
                .order_by('-submit_date')
                .prefetch_related('content_object'))


class PostCommentsFeed(CommentsFeedBase):

    def get_object(self, request, blog, post):
        return get_object_or_404(Post,
            blog__name=blog, blog__language=request.LANGUAGE_CODE, name=post)

    def link(self, post):
        return "http://{}/#comment_header".format(post.get_absolute_url())

    def title(self, post):
        return _("Comments on \"{}\"").format(post.title)

    description = title

    def items(self, post):
        CommentModel = comments.get_model()
        return (CommentModel.objects.filter(
            is_public=True, is_removed=False,
            content_type=ContentType.objects.get_for_model(Post),
            object_pk=post.id)
              .order_by('-submit_date')
              .prefetch_related('content_object'))


class PageCommentsFeed(CommentsFeedBase):

    def get_object(self, request, page):
        return get_object_or_404(
            Page, language=request.LANGUAGE_CODE, name=page)

    def link(self, page):
        return "http://{}/#comment_header".format(page.get_absolute_url())

    def title(self, page):
        return _("Comments on \"{}\"").format(page.title)

    description = title

    def items(self, page):
        CommentModel = comments.get_model()
        return (CommentModel.objects.filter(
            is_public=True, is_removed=False,
            content_type=ContentType.objects.get_for_model(Page),
            object_pk=page.id)
                .order_by('-submit_date')
                .prefetch_related('content_object'))
