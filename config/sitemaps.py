from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import BlogPost

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'
    i18n = True

    def items(self):
        return ['pages:index', 'pages:agb', 'pages:datenschutz', 'pages:impressum']

    def location(self, item):
        return reverse(item)

class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    # Enable i18n sitemap support
    i18n = True

    def items(self):
        return BlogPost.objects.filter(is_active=True, is_indexable=True)

    def lastmod(self, obj):
        return obj.updated_at
