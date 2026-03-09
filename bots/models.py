from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

class BotCategory(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_("Category Name"), max_length=100),
        description=models.TextField(_("Description"), blank=True, null=True),
    )
    base_price = models.DecimalField(_("Base Price (€)"), max_digits=8, decimal_places=2, default=0.00)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Bot Category")
        verbose_name_plural = _("Bot Categories")

    def __str__(self):
        return self.safe_translation_getter("name", any_language=True) or f"Category #{self.pk}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid & Drafted'),
        ('in_progress', 'Development In Progress'),
        ('delivered', 'Delivered'),
    ]

    order_id = models.CharField(_("Order ID"), max_length=50, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', null=True, blank=True, verbose_name=_("User"))
    category = models.ForeignKey(BotCategory, on_delete=models.SET_NULL, null=True, verbose_name=_("Bot Category"))
    
    # AI Scoping Results
    requirements_json = models.JSONField(_("AI Generated Requirements"), default=dict, blank=True)
    consulting_requested = models.BooleanField(_("Consulting Upsell Selected"), default=False)
    contact_info = models.CharField(_("Contact Information"), max_length=255, blank=True)
    
    # Financials
    total_price = models.DecimalField(_("Total Price (€)"), max_digits=10, decimal_places=2, default=0.00)
    is_hosted = models.BooleanField(_("Managed Hosting"), default=True)
    monthly_fee = models.DecimalField(_("Monthly Hosting Fee (€)"), max_digits=8, decimal_places=2, default=0.00)
    
    # Fulfillment & Management
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    draft_file_path = models.CharField(_("Draft File Path"), max_length=255, blank=True)
    source_code_url = models.CharField(_("Source Code URL/Path"), max_length=500, blank=True, help_text=_("Link to the clean source code for non-hosted bots"))
    is_active = models.BooleanField(_("Bot Active"), default=True, help_text=_("Toggle bot status on or off"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Bot Order")
        verbose_name_plural = _("Bot Orders")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_id} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            import uuid
            # Generating unique ID like Order_7392_TelegramBot
            short_id = str(uuid.uuid4().int)[:4]
            cat_name = self.category.name if self.category else "CustomBot"
            self.order_id = f"Order_{short_id}_{cat_name}".replace(" ", "")
        super().save(*args, **kwargs)

class BotAdjustment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='adjustments')
    message = models.TextField(_("Adjustment Request"))
    is_from_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Bot Adjustment")
        verbose_name_plural = _("Bot Adjustments")
        ordering = ['created_at']

    def __str__(self):
        return f"Adj for {self.order.order_id} at {self.created_at}"
