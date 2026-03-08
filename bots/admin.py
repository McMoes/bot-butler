from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import BotCategory, Order

@admin.register(BotCategory)
class BotCategoryAdmin(TranslatableAdmin):
    list_display = ('name', 'base_price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('translations__name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'category', 'status', 'total_price', 'consulting_requested', 'created_at')
    list_filter = ('status', 'consulting_requested', 'category')
    search_fields = ('order_id', 'contact_info')
    readonly_fields = ('order_id', 'created_at', 'updated_at', 'draft_file_path')
