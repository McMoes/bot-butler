from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import Ticket, TicketMessage
from .forms import TicketCreateForm, TicketReplyForm

class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'support/ticket_list.html'
    context_object_name = 'tickets'

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return redirect('support:admin_ticket_list')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).order_by('-updated_at')

class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = 'support/ticket_form.html'
    success_url = reverse_lazy('support:ticket_list')

    def form_valid(self, form):
        # Set user
        ticket = form.save(commit=False)
        ticket.user = self.request.user
        ticket.status = 'OPEN'
        ticket.save()
        
        # Create initial message
        TicketMessage.objects.create(
            ticket=ticket,
            sender=self.request.user,
            message=form.cleaned_data['initial_message']
        )
        messages.success(self.request, "Dein Ticket wurde erfolgreich erstellt.")
        return redirect('support:ticket_detail', pk=ticket.id)

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'support/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        # Superusers can see all, standard users only their own
        if self.request.user.is_superuser:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reply_form'] = TicketReplyForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = TicketReplyForm(request.POST)
        
        if form.is_valid():
            reply = form.save(commit=False)
            reply.ticket = self.object
            reply.sender = request.user
            reply.save()

            # Logic: If admin replies, status = ANSWERED. If user replies, status = OPEN.
            if request.user.is_superuser:
                self.object.status = 'ANSWERED'
            else:
                self.object.status = 'OPEN'
            self.object.save()
            
            messages.success(request, "Antwort erfolgreich gesendet.")
            return redirect('support:ticket_detail', pk=self.object.id)
            
        context = self.get_context_data(object=self.object)
        context['reply_form'] = form
        return self.render_to_response(context)

class TicketCloseView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        if request.user.is_superuser:
            ticket = get_object_or_404(Ticket, pk=pk)
        else:
            ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
            
        ticket.status = 'CLOSED'
        ticket.save()
        messages.success(request, "Das Ticket wurde geschlossen.")
        return redirect('support:ticket_detail', pk=ticket.id)

class AdminTicketListView(UserPassesTestMixin, ListView):
    model = Ticket
    template_name = 'support/admin_ticket_list.html'
    context_object_name = 'tickets'

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        # Show all tickets that are not closed, ordered so OPEN (needs attention) are top
        return Ticket.objects.exclude(status='CLOSED').order_by('status', '-updated_at')
