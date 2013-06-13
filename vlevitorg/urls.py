from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.views.generic.simple import redirect_to

from vlevitorg import settings

admin.autodiscover()


urlpatterns = patterns('',
    # favicon for apps ignoring icon link in html
    url(r'^favicon.ico$', redirect_to,
        {'url': "{}/{}".format(settings.STATIC_URL, 'images/favicon.ico')}),
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^$', redirect_to, {'url': "/blog/tech/"}),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += i18n_patterns('',
    url('', include('vlblog.urls')),
)

# i18n patterns can be only in top-level URLConf
# so non-i18n patterns can't be moved to the app's URLConf

urlpatterns += patterns('vlblog.views.tools',
    url(r'^import/(?P<what>blog|pages|all)/', 'import_entries'),
    url(r'^pingme', 'pingme'),
    url(r'^error', 'internal_error'),
)

urlpatterns += patterns('vlblog.views.comments',
    url(r'^import/comments/', 'import_comments'),
    url(r'^export/comments/', 'export_comments'),
)

urlpatterns += patterns('',
    # not possible to customize urls from the comments app?
    url(r'^comments/preview/$', 'threadedcomments.views.preview_comment'),
    url(r'^comments/post/$', 'threadedcomments.views.post_comment'),
    url(r'^comments/', include('django.contrib.comments.urls')),

)
