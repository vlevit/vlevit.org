from django.contrib.sitemaps import Sitemap
from vlblog.models import Post, Page, Blog


class BlogMap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Blog.objects.order_by()


class PostMap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Post.objects.order_by('-created')


class PageMap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Page.objects.all()


sitemaps = {
    'blogs': BlogMap,
    'posts': PostMap,
    'pages': PageMap
}
