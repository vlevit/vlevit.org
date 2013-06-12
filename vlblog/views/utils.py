from django.conf import settings
from django.http import HttpResponse, HttpRequest


def require_key(func):
    def wrapper(*args, **kwargs):
        if len(args) < 1 or not isinstance(args[0], HttpRequest):
            raise TypeError("first argument must be HttpRequest instance")
        req = args[0]
        if req.method != 'GET' and req.method != 'POST':
            return HttpResponse("Wrong type of request: {}".format(req.method),
                                status=404, content_type="text/plain")
        if not ('key' in req.REQUEST and
                req.REQUEST['key'] == settings.SECRET_URL_KEY or
                settings.SECRET_URL_KEY in req.path):
            return HttpResponse("Key is not specified or incorrect",
                                status=404, content_type="text/plain")
        return func(*args, **kwargs)
    return wrapper
