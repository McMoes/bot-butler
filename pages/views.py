from django.views.generic import TemplateView
from bots.models import BotCategory

class IndexView(TemplateView):
    template_name = 'pages/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch only active categories
        context['categories'] = BotCategory.objects.filter(is_active=True)
        return context
