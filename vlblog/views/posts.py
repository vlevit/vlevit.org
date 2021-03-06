from django.http import Http404
from django.shortcuts import render, get_object_or_404

from vlblog import models
from vlblog.utils import LastPagePaginator


def post(request, blog, post):
    posts = models.Post.objects.filter(
        blog__name=blog, blog__language=request.LANGUAGE_CODE,
        name=post).select_related()
    if posts:
        post_obj = posts[0]
        languages = models.Post.objects.filter(
            blog__name=blog, name=post).values_list('blog__language',
                                                    flat=True)
        tags = post_obj.tags.all().select_related()
        return render(request, post_obj.blog.template,
                      {'post': post_obj, 'blog': post_obj.blog,
                       'tags': tags, 'languages': languages})
    else:
        raise Http404


def post_list(request, blog, tag=None, page=1):
    blog_obj = get_object_or_404(
        models.Blog, name=blog, language=request.LANGUAGE_CODE)
    foreign_blog_obj = models.Blog.objects.filter(name=blog).exclude(
        language=request.LANGUAGE_CODE).first()
    posts = models.Post.objects.filter(blog=blog_obj)
    if tag:
        posts = posts.filter(tags__name__iexact=tag)
        foreign_posts = models.Post.objects.filter(
            blog=foreign_blog_obj, tags__name__iexact=tag)
    else:
        foreign_posts = models.Post.objects.filter(blog=foreign_blog_obj)
    posts = posts.select_related().prefetch_related('tags')
    foreign_posts = foreign_posts.select_related().prefetch_related('tags')
    posts = LastPagePaginator(posts, blog_obj.per_page).page(page)
    if foreign_blog_obj:
        foreign_posts = LastPagePaginator(foreign_posts,
                                          foreign_blog_obj.per_page).page(page)
    if posts:
        post_obj = posts[0]
        blog_obj = post_obj.blog
        tags = models.Tag.objects.filter(
            blog=blog_obj, n_posts__gt=1).select_related()
        return render(request, blog_obj.list_template,
                      {'blog': blog_obj, 'posts': posts,
                       'foreign_posts': foreign_posts,
                       'tags': tags, 'page': page})
    else:
        raise Http404


def page(request, page):
    page_obj = get_object_or_404(models.Page, name=page,
                                 language=request.LANGUAGE_CODE)
    return render(request, page_obj.template, {'page': page_obj})
