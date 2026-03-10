from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(TranslatableAdmin):
    list_display = ('title', 'author', 'published_at', 'is_active', 'is_indexable', 'all_languages_column')
    list_filter = ('is_active', 'is_indexable', 'published_at', 'author')
    search_fields = ('translations__title', 'translations__content', 'translations__slug')
    
    # Translatable fields configuration
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'featured_image', 'featured_image_alt', 'author'),
        }),
        ('Status & Visibility', {
            'fields': ('published_at', 'is_active', 'is_indexable'),
            'classes': ('collapse',),
        }),
        ('SEO Metadata', {
            'fields': ('meta_title', 'meta_description', 'keywords'),
            'classes': ('collapse',),
        }),
    )
    
    # Important: Do not use prepopulated_fields directly on translated fields (e.g., 'slug': ('title',)) 
    # to avoid 500 errors with Parler Admin. The slug field will remain editable manually.
