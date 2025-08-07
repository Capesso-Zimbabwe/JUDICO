from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'hr_management'

urlpatterns = [
    path('', lambda request: redirect('hr_management:dashboard'), name='hr_root'),
    path('dashboard/', views.hr_dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/update/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('leave/', views.leave_management, name='leave_management'),
    path('leave/create-modal/', views.leave_create_modal, name='leave_create_modal'),
    path('performance/', views.performance_reviews, name='performance_reviews'),
    path('performance/create-modal/', views.create_review_modal, name='create_review_modal'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/create-modal/', views.create_user_modal, name='create_user_modal'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('lawyers/', views.manage_lawyers, name='manage_lawyers'),
    path('lawyers/toggle/<int:user_id>/', views.toggle_lawyer, name='toggle_lawyer'),
    path('clients/toggle/<int:user_id>/', views.toggle_client, name='toggle_client'),
    path('timesheets/', views.time_sheets, name='time_sheets'),
]