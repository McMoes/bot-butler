from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('bot/<int:pk>/', views.BotDetailView.as_view(), name='bot_detail'),
    path('agb/', views.AgbView.as_view(), name='agb'),
    path('datenschutz/', views.DatenschutzView.as_view(), name='datenschutz'),
    path('impressum/', views.ImpressumView.as_view(), name='impressum'),
]
