from django.urls import path
from . import views

app_name = 'lawyer_portal'

urlpatterns = [
    path('', views.lawyer_check, name='lawyer_check'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/update-status/', views.update_task_status, name='update_task_status'),
    path('transactions/', views.transactions, name='transactions'),
    path('documents/', views.documents, name='documents'),
    path('communications/', views.communications, name='communications'),
    path('clients/', views.clients, name='clients'),
    path('create-profile/', views.create_lawyer_profile, name='create_lawyer_profile'),
    path('edit-profile/', views.edit_lawyer_profile, name='edit_profile'),
]

