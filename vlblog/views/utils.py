from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse, HttpRequest
from django.views.generic.base import RedirectView
from django.utils.translation import activate


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


class LanguageRedirectView(RedirectView):

    permanent = False
    language = None

    def get_redirect_url(self, **kwargs):
        if self.url:
            language = self.language or self.request.LANGUAGE_CODE
            self.url = '/{}{}'.format(language, self.url)
            return super(LanguageRedirectView, self).get_redirect_url(**kwargs)
        else:
            return None


class LegacyRedirectView(RedirectView):

    permanent = True
    language = None
    view = None

    def get_redirect_url(self, **kwargs):
        if self.language:
            activate(self.language)
        self.url = reverse(self.view, kwargs=kwargs).replace('%', '%%')
        return super(LegacyRedirectView, self).get_redirect_url(**kwargs)
