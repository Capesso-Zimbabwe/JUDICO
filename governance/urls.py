from django.urls import path
from . import views

app_name = 'governance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('policies/', views.policies, name='policies'),
    path('policies/create/', views.create_policy, name='create_policy'),
    path('policies/<int:policy_id>/', views.view_policy, name='view_policy'),
    path('policies/<int:policy_id>/edit/', views.edit_policy, name='edit_policy'),
    path('policies/<int:policy_id>/delete/', views.delete_policy, name='delete_policy'),
    path('meetings/', views.meetings, name='meetings'),
    path('meetings/create/', views.create_meeting, name='create_meeting'),
    path('meetings/<int:meeting_id>/', views.view_meeting, name='view_meeting'),
    path('meetings/<int:meeting_id>/edit/', views.edit_meeting, name='edit_meeting'),
    path('meetings/<int:meeting_id>/delete/', views.delete_meeting, name='delete_meeting'),
    path('meetings/<int:meeting_id>/minutes/', views.update_meeting_minutes, name='update_meeting_minutes'),
    path('reports/', views.reports, name='reports'),
    path('reports/create/', views.create_report, name='create_report'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/delete/', views.delete_report, name='delete_report'),
]