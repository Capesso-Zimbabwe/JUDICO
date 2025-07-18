from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'communication'

urlpatterns = [
    path('', lambda request: redirect('communication:dashboard'), name='communication_root'),
    path('dashboard/', views.communication_dashboard, name='dashboard'),
    path('messages/', views.message_list, name='messages'),
    path('messages/create/', views.message_create, name='message_create'),
    path('notifications/', views.notification_list, name='notifications'),
    path('settings/', views.communication_settings, name='settings'),
]