from django.contrib.sitemaps import Sitemap
from vlblog.models import Post, Page


class BlogMap(Sitemap):
    changefreq = "monthly"

    def items(self):
        return Post.objects.order_by('-created')


class PageMap(Sitemap):
    changefreq = "monthly"

    def items(self):
        return Page.objects.all()


sitemaps = {
    'posts': BlogMap,
    'pages': PageMap
}
