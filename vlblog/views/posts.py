from django.shortcuts import render, get_object_or_404, get_list_or_404

from vlblog import models


def post(request, blog, post):
    blog_obj = get_object_or_404(models.Blog, name=blog,
                                 language=request.LANGUAGE_CODE)
    post_obj = get_object_or_404(models.Post, blog=blog_obj, name=post)
    tags = post_obj.tags.all()
    return render(request, blog_obj.template, {'post': post_obj, 'tags': tags})


def post_list(request, blog, tag=None):
    blog_obj = get_object_or_404(models.Blog, name=blog,
                                 language=request.LANGUAGE_CODE)
    if tag:
        posts = get_list_or_404(models.Post, blog=blog_obj, tags__name=tag)
    else:
        posts = get_list_or_404(models.Post, blog=blog_obj)
    tags = models.Tag.objects.filter(blog=blog_obj, n_posts__gt=1)
    return render(request, blog_obj.list_template,
                  {'blog': blog_obj, 'posts': posts, 'tags': tags})


def page(request, page):
    page_obj = get_object_or_404(models.Page, name=page,
                                 language=request.LANGUAGE_CODE)
    return render(request, page_obj.template, {'page': page_obj})
