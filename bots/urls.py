from django.urls import path
from . import views

app_name = 'bots'

urlpatterns = [
    path('checkout/', views.CreateOrderView.as_view(), name='checkout'),
]
