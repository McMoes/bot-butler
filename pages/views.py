from django.views.generic import TemplateView, CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from bots.models import BotCategory, Order

class IndexView(TemplateView):
    template_name = 'pages/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch only active categories
        context['categories'] = BotCategory.objects.filter(is_active=True)
        return context

class AgbView(TemplateView):
    template_name = 'pages/agb.html'

class DatenschutzView(TemplateView):
    template_name = 'pages/datenschutz.html'

class ImpressumView(TemplateView):
    template_name = 'pages/impressum.html'

from django.contrib.auth import login

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    
    def form_valid(self, form):
        # Save user and log them in immediately
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
        
    def get_success_url(self):
        # Respect 'next' parameter so users go back to their chat/checkout
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('pages:dashboard')

class DashboardView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'pages/dashboard.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class BotDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'pages/bot_detail.html'
    context_object_name = 'bot'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
