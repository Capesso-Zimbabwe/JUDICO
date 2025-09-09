
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),  # Use our custom login view
    path('logout/', views.logout_view, name='logout'),  # Use our custom logout view
    # Removed the register path
    
    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='authentication/password_reset_form.html'), 
         name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), 
         name='password_reset_complete'),
    
    # Time tracking API endpoints
    path('api/start-tracking/', views.start_time_tracking, name='start_time_tracking'),
    path('api/stop-tracking/', views.stop_time_tracking, name='stop_time_tracking'),
    path('api/tracking-status/', views.get_time_tracking_status, name='get_time_tracking_status'),
]