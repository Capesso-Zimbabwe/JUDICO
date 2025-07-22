from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'communication'

urlpatterns = [
    path('', lambda request: redirect('communication:dashboard'), name='communication_root'),
    path('dashboard/', views.communication_dashboard, name='dashboard'),
    path('messages/', views.message_list, name='messages'),
    path('messages/new/', views.new_conversation, name='new_conversation'),
    path('api/messages/<int:user_id>/', views.message_detail_api, name='message_detail_api'),
    path('api/messages/<int:user_id>/send/', views.send_message_api, name='send_message_api'),
    path('notifications/', views.notification_list, name='notifications'),
    path('settings/', views.communication_settings, name='settings'),
    path('meetings/', views.meeting_list, name='meeting_list'),
    path('meetings/create/', views.meeting_create, name='meeting_create'),
    path('meetings/<int:meeting_id>/', views.meeting_detail, name='meeting_detail'),
    path('api/calendar/', views.calendar_api, name='calendar_api'),
    path('api/notifications/count/', views.notification_count_api, name='notification_count_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
]