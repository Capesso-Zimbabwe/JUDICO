from django.urls import path
from . import views

app_name = 'client_portal'

urlpatterns = [
    path('', views.client_check, name='client_check'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('projects/', views.projects, name='projects'),
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('documents/', views.documents, name='documents'),
    path('communications/', views.communications, name='communications'),
    path('profile/', views.profile, name='profile'),
]