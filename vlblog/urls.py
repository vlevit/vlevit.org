from django.conf.urls import patterns, url


urlpatterns = patterns('vlblog.views',
    url(r'^blog/(?P<blog>[\w-]+)/?$', 'post_list', name='post_list'),
    url(r'^blog/(?P<blog>[\w-]+)/tag/(?P<tag>.*)', 'post_list', name='post_list_tag'),
    url(r'^blog/(?P<blog>[\w-]+)/(?P<post>[\w-]+)', 'post'),
)
