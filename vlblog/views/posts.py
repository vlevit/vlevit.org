from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, get_list_or_404

from vlevitorg import settings
from vlblog import models
from vlblog import scanner


def scan(request):
    if 'key' not in request.GET or \
            request.GET['key'] != settings.SECRET_URL_KEY:
        return HttpResponse("Key is not specified or incorrect",
                            content_type="text/plain")
    force_reimport = False
    if 'force_reimport' in request.GET:
        force_reimport = True
    blog_importer = scanner.BlogImporter(settings.CONTENT_DIR)
    blog_importer.import_all(force_reimport=force_reimport)
    return HttpResponse('See log', content_type="text/plain")


def post(request, blog, post):
    blog_obj = get_object_or_404(models.Blog, name=blog,
                                 language=request.LANGUAGE_CODE)
    post_obj = get_object_or_404(models.Post, blog=blog_obj, name=post)
    return render(request, 'tech_post.html', {'post': post_obj})


def post_list(request, blog, tag=None):
    blog_obj = get_object_or_404(models.Blog, name=blog,
                                 language=request.LANGUAGE_CODE)
    if tag:
        posts = get_list_or_404(models.Post, blog=blog_obj, tags__name=tag)
    else:
        posts = get_list_or_404(models.Post, blog=blog_obj)
    return render(request, 'tech_post_list.html',
                  {'blog': blog_obj, 'posts': posts})
