from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

class BlogPost(TranslatableModel):
    translations = TranslatedFields(
        title = models.CharField(_("Title"), max_length=200),
        content = models.TextField(_("Content")),
        # Perfected SEO Fields (Translatable)
        slug = models.SlugField(_("Slug"), max_length=255, unique=True, help_text=_("URL identifier for this language")),
        meta_title = models.CharField(_("Meta Title (SEO)"), max_length=200, blank=True),
        meta_description = models.TextField(_("Meta Description (SEO)"), blank=True),
        keywords = models.CharField(_("Keywords (SEO)"), max_length=500, blank=True, help_text=_("Comma separated keywords")),
        featured_image_alt = models.CharField(_("Image Alt Text (SEO)"), max_length=200, blank=True, help_text=_("Accessibility and Image SEO describing the featured image")),
    )
    
    # Shared Fields
    featured_image = models.ImageField(_("Featured Image (OG)"), upload_to='blog/images/', blank=True, null=True)
    author = models.CharField(_("Author"), max_length=100, default="Admin")
    
    # Freshness and Timestamps
    published_at = models.DateTimeField(_("Published At"), default=timezone.now)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    # Visibility and Crawl Control
    is_active = models.BooleanField(_("Active"), default=True)
    is_indexable = models.BooleanField(_("Indexable (SEO)"), default=True, help_text=_("Allow search engines to index this post. Uncheck to add noindex tag."))

    class Meta:
        verbose_name = _("Blog Post")
        verbose_name_plural = _("Blog Posts")

    def __str__(self):
        return self.safe_translation_getter('title', any_language=True)

    @property
    def display_title(self):
        return self.safe_translation_getter('title', any_language=True) or f"Post #{self.pk}"

    @property
    def display_content(self):
        return self.safe_translation_getter('content', any_language=True) or ""

    @property
    def display_meta_title(self):
        return self.safe_translation_getter('meta_title', any_language=True) or self.display_title

    @property
    def display_meta_description(self):
        return self.safe_translation_getter('meta_description', any_language=True) or self.display_content[:150]
        
    @property
    def display_image_alt(self):
        return self.safe_translation_getter('featured_image_alt', any_language=True) or self.display_title

    def get_absolute_url(self):
        from django.urls import reverse
        slug = self.safe_translation_getter('slug', any_language=True)
        if slug:
            return reverse('blog:post_detail', kwargs={'slug': slug})
        return "#"

    def get_json_ld(self):
        import json
        from django.conf import settings
        
        # Determine base URL
        try:
            from django.contrib.sites.models import Site
            domain = Site.objects.get_current().domain
            base_url = f"https://{domain}"
        except Exception:
            base_url = getattr(settings, 'SITE_URL', 'https://bot-butler.com')
            
        image_url = f"{base_url}{self.featured_image.url}" if self.featured_image else ""
        
        data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": self.display_title,
            "description": self.display_meta_description,
            "image": [image_url],
            "datePublished": self.published_at.isoformat(),
            "dateModified": self.updated_at.isoformat(), # Added Freshness Factor
            "author": [{
                "@type": "Organization",
                "name": self.author
            }],
            "publisher": {
                "@type": "Organization",
                "name": "Bot Butler",
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{base_url}/static/images/logo.png"
                }
            }
        }
        return json.dumps(data)
