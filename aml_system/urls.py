from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'aml_system'

urlpatterns = [
    path('', lambda request: redirect('aml_system:dashboard'), name='aml_root'),
    path('dashboard/', views.aml_dashboard, name='dashboard'),
    
    # Screening URLs
    path('screening/', views.screening_list, name='screening'),
    path('screening/create/', views.screening_create, name='screening_create'),
    path('screening/<int:pk>/', views.screening_detail, name='screening_detail'),
    path('screening/<int:pk>/update/', views.screening_update, name='screening_update'),
    
    # Entity URLs
    path('entity/create/', views.entity_create, name='entity_create'),
    
    # Alert URLs
    path('alert/<int:pk>/', views.alert_detail, name='alert_detail'),
    path('alert/<int:pk>/escalate/', views.alert_escalate, name='alert_escalate'),
    
    # Other URLs
    path('monitoring/', views.monitoring_list, name='monitoring'),
    path('reports/', views.reports_list, name='reports'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/download/', views.report_download, name='report_download'),
]