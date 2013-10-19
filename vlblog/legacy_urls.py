from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from vlblog.views.utils import LegacyRedirectView


redirect = RedirectView.as_view
legacy_redirect = LegacyRedirectView.as_view

urlpatterns = patterns('',
    # Blog Feed
    url(r"^feeds/posts/default", redirect(url='/ru/blog/tech.rss')),
    # Comments Feed
    url(r"^feeds/comments/default",
        redirect(url='/ru/blog/tech/comments.rss')),

    # Posts
    url(r'2011/04/xatk.html', redirect(url='/ru/blog/tech/xatk')),
    url(r'2011/04/adler32.html', redirect(url='/ru/blog/tech/adler32')),
    url(r'2011/04/wuala.html', redirect(url='/ru/blog/tech/wuala')),
    url(r'2011/06/vimperator.html', redirect(url='/ru/blog/tech/vimperator')),
    url(r'2011/08/xchainkeys.html', redirect(url='/ru/blog/tech/xchainkeys')),
    url(r'2011/09/rdfind.html', redirect(url='/ru/blog/tech/rdfind')),
    url(r'2011/12/transmission-zotac-zbox-sd-id12-wi-fi.html',
        redirect(url='/ru/blog/tech/transmission-batch-move')),
    url(r'2012/01/flac-ogg-vorbis.html',
        redirect(url='/ru/blog/tech/flacconvert')),
    url(r'2012/03/xatk-01.html', redirect(url='/ru/blog/tech/xatk-1')),
    url(r'2012/06/unison-unisync.html', redirect(url='/ru/blog/tech/unisync')),
    url(r'2013/01/mpd-ncmpcpp-urxvt.html', redirect(url='/ru/blog/tech/mnuc')),

    # Tags
    # "key bindings" tag -> "keys" tag
    url(ur'^search/label/'
        u'\u0441\u043e\u0447\u0435\u0442\u0430\u043d\u0438\u044f '
        u'\u043a\u043b\u0430\u0432\u0438\u0448',
        redirect(url='/ru/blog/tech/tag/'
                 '%%D0%%BA%%D0%%BB%%D0%%B0%%D0%%B2%%D0%%B8%%D1%%88%%D0%%B8')),
    # Other Tags
    url(r'^search/label/(?P<tag>.*)',
        legacy_redirect(view='post_list_tag', language='ru'),
        kwargs={'blog': 'tech'}),

    # Archive
    url(r'.*archive.html$', redirect(url='/ru/blog/tech/')),
    # Search
    url(r'^search$', redirect(url='/ru/blog/tech/')),
)
