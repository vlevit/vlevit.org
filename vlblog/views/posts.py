from django.http import Http404
from django.shortcuts import render, get_object_or_404

from vlblog import models


def post(request, blog, post):
    posts = models.Post.objects.filter(
        blog__name=blog, blog__language=request.LANGUAGE_CODE,
        name=post).select_related()
    if posts:
        post_obj = posts[0]
        tags = post_obj.tags.all().select_related()
        return render(request, post_obj.blog.template,
                      {'post': post_obj, 'tags': tags})
    else:
        raise Http404


def post_list(request, blog, tag=None):
    posts = models.Post.objects.filter(
        blog__name=blog, blog__language=request.LANGUAGE_CODE)
    posts = posts.select_related().defer('body')
    if posts:
        post_obj = posts[0]
        blog_obj = post_obj.blog
        tags = models.Tag.objects.filter(
            blog=blog_obj, n_posts__gt=1).select_related()
        return render(request, blog_obj.list_template,
                      {'blog': blog_obj, 'posts': posts, 'tags': tags})
    else:
        raise Http404


def page(request, page):
    page_obj = get_object_or_404(models.Page, name=page,
                                 language=request.LANGUAGE_CODE)
    return render(request, page_obj.template, {'page': page_obj})
