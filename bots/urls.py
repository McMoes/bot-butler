from django.urls import path
from . import views

app_name = 'bots'

urlpatterns = [
    path('checkout/', views.CreateOrderView.as_view(), name='checkout'),
    path('builder/chat/', views.BotBuilderChatView.as_view(), name='builder_chat'),
    path('support/chat/', views.SupportChatWebhookView.as_view(), name='support_chat'),
    path('<str:order_id>/toggle/', views.ToggleBotStatusView.as_view(), name='toggle'),
    path('<str:order_id>/adjust/', views.BotAdjustmentView.as_view(), name='adjust'),
]
