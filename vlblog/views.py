from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404

from vlblog import models
from vlblog import scanner


def scan(request):
    force_reimport = False
    if 'force_reimport' in request.GET:
        force_reimport = True
    scanner.scan(force_reimport=force_reimport)
    return HttpResponse('See log', content_type="text/plain")


def post(request, blog, post):
    blog_obj = get_object_or_404(models.Blog, name=blog)
    post_obj = get_object_or_404(
        models.Post, language=request.LANGUAGE_CODE, blog=blog_obj, name=post)
    return render_to_response('tech_post.html', {'post': post_obj})
