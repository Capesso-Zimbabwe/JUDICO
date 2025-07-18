from django.urls import path
from .admin import custom_admin_site
from . import views

app_name = 'admin_portal'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-lawyers/', views.manage_lawyers, name='manage_lawyers'),
    path('toggle-lawyer/<int:user_id>/', views.toggle_lawyer, name='toggle_lawyer'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('toggle-client/<int:user_id>/', views.toggle_client, name='toggle_client'),
    path('create-user/', views.create_user, name='create_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    
    # Reports URLs
    path('reports/', views.reports, name='reports'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('reports/view/<int:report_id>/', views.view_report, name='view_report'),
    path('reports/download/<int:report_id>/', views.download_report, name='download_report'),
    
    # Move the custom admin site to a specific path
    path('django-admin/', custom_admin_site.urls),
]