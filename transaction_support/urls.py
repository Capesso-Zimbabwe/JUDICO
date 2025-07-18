from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'transaction_support'

urlpatterns = [
    path('', lambda request: redirect('transaction_support:dashboard'), name='transaction_root'),
    path('dashboard/', views.transaction_dashboard, name='dashboard'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('monitoring/', views.transaction_monitoring, name='monitoring'),
    path('reports/', views.transaction_reports, name='reports'),
]