from django.contrib.sitemaps import Sitemap
from blog.models import BlogPost

class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    # Enable i18n sitemap support
    i18n = True

    def items(self):
        return BlogPost.objects.filter(is_active=True, is_indexable=True)

    def lastmod(self, obj):
        return obj.updated_at
