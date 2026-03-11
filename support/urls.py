from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/new/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:pk>/close/', views.TicketCloseView.as_view(), name='ticket_close'),
    path('admin-dashboard/tickets/', views.AdminTicketListView.as_view(), name='admin_ticket_list'),
]
