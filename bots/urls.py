from django.urls import path
from . import views

app_name = 'bots'

urlpatterns = [
    path('checkout/', views.CreateOrderView.as_view(), name='checkout'),
    path('<str:order_id>/toggle/', views.ToggleBotStatusView.as_view(), name='toggle'),
    path('<str:order_id>/adjust/', views.BotAdjustmentView.as_view(), name='adjust'),
]
