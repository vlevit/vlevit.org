from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin


admin.autodiscover()


urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^scan/', 'vlblog.views.scan'),
    url(r'^admin/', include(admin.site.urls)),
)


urlpatterns += i18n_patterns('',
    url(r'^(?P<blog>[\w-]+)/(?P<post>[\w-]+)', 'vlblog.views.post'),
)
