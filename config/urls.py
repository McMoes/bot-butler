from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from bots import views as bots_views
from config.sitemaps import BlogSitemap, StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('rosetta/', include('rosetta.urls')),
    path('webhooks/stripe/', bots_views.StripeWebhookView.as_view(), name='stripe_webhook'),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('api/bots/', include('bots.urls')),
    path('blog/', include('blog.urls')),
    path('', include('pages.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
