from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'compliance'

urlpatterns = [
    path('', lambda request: redirect('compliance:dashboard'), name='compliance_root'),
    path('dashboard/', views.compliance_dashboard, name='dashboard'),
    path('calendar/', views.regulatory_calendar, name='regulatory_calendar'),
    path('requirements/', views.requirements_list, name='requirements'),
    path('requirements/create/', views.create_requirement, name='create_requirement'),
    path('audits/', views.audits_list, name='audits'),
    path('audits/create/', views.create_audit, name='create_audit'),
    path('audits/<int:audit_id>/update/', views.update_audit, name='update_audit'),
    path('audits/<int:audit_id>/details/', views.audit_details, name='audit_details'),
    path('reports/', views.compliance_reports, name='reports'),
]