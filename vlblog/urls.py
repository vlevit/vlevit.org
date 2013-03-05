from django.conf.urls import patterns, url


urlpatterns = patterns('vlblog.views',
    url(r'^blog/(?P<blog>[\w-]+)/(?P<post>[\w-]+)', 'post'),
)
