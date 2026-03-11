from django import forms
from .models import Ticket, TicketMessage

class TicketCreateForm(forms.ModelForm):
    initial_message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Beschreibe dein Problem oder deine Frage im Detail...'}),
        label="Nachricht",
        required=True
    )

    class Meta:
        model = Ticket
        fields = ['subject']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kurzer Betreff'}),
        }

class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Deine Antwort hier eingeben...'}),
        }
