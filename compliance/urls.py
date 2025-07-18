from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'compliance'

urlpatterns = [
    path('', lambda request: redirect('compliance:dashboard'), name='compliance_root'),
    path('dashboard/', views.compliance_dashboard, name='dashboard'),
    path('requirements/', views.requirements_list, name='requirements'),
    path('audits/', views.audits_list, name='audits'),
    path('reports/', views.compliance_reports, name='reports'),
]