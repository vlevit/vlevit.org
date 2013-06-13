from django.conf.urls import patterns, url
from django.views.generic.simple import redirect_to

from vlblog import feeds

urlpatterns = patterns('vlblog.views.posts',

    # Pages
    url(r'^page/(?P<page>[\w-]+)/$', 'page', name='page'),

    # Redirections
    url(r'^blog/$', redirect_to, {'url': "/blog/tech/"}),

    # Feeds
    url(r'^blog/?\.rss$', feeds.SiteFeed(), name='site_feed'),
    url(r'^blog/comments\.rss$', feeds.SiteCommentsFeed(),
        name='site_comments_feed'),
    url(r'^blog/(?P<blog>[\w-]+)/?\.rss$', feeds.BlogFeed(), name='blog_feed'),
    url(r'^blog/(?P<blog>[\w-]+)/comments\.rss$', feeds.BlogCommentsFeed(),
        name='blog_comments_feed'),
    url(r'^blog/(?P<blog>[\w-]+)/(?P<post>[\w-]+)(?:/comments)?\.rss$',
        feeds.PostCommentsFeed(), name='post_comments_feed'),

    # Blog Posts
    url(r'^blog/(?P<blog>[\w-]+)/$', 'post_list', name='post_list'),
    url(r'^blog/(?P<blog>[\w-]+)/tag/(?P<tag>.*)', 'post_list',
        name='post_list_tag'),
    url(r'^blog/(?P<blog>[\w-]+)/(?P<post>[\w-]+)', 'post', name='post'),
)
