from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin


admin.autodiscover()


urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^scan/', 'vlblog.views.scan'),
    url(r'^admin/', include(admin.site.urls)),
    # impossible to customize urls from the comments app?
    url(r'^comments/preview/$', 'threadedcomments.views.preview_comment'),
    url(r'^comments/post/$', 'threadedcomments.views.post_comment'),
    url(r'^comments/', include('django.contrib.comments.urls')),
)


urlpatterns += i18n_patterns('',
    url('', include('vlblog.urls')),
)
