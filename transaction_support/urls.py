from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'transaction_support'

urlpatterns = [
    # Main navigation
    path('', lambda request: redirect('transaction_support:dashboard'), name='transaction_root'),
    path('dashboard/', views.transaction_dashboard, name='dashboard'),
    
    # Transaction CRUD operations
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list_cbv'),
    path('transactions/list/', views.transaction_list, name='transaction_list'),  # Legacy redirect
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction_create_cbv'),
    path('transactions/new/', views.transaction_create, name='transaction_create'),  # Legacy redirect
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    
    # Transaction Entity Management
    path('transactions/<int:transaction_pk>/entities/add/', views.TransactionEntityCreateView.as_view(), name='entity_create'),
    
    # Document Management
    path('transactions/<int:transaction_pk>/documents/', views.TransactionDocumentListView.as_view(), name='document_list'),
    path('transactions/<int:transaction_pk>/documents/create/', views.TransactionDocumentCreateView.as_view(), name='document_create'),
    path('transactions/<int:transaction_pk>/documents/bulk-upload/', views.bulk_document_upload, name='bulk_document_upload'),
    path('documents/<int:pk>/', views.TransactionDocumentDetailView.as_view(), name='document_detail'),
    path('documents/<int:pk>/download/', views.document_download, name='document_download'),
    path('documents/<int:pk>/new-version/', views.document_version_create, name='document_version_create'),
    path('documents/<int:pk>/review-toggle/', views.document_review_toggle, name='document_review_toggle'),
    
    # Workflow Management
    path('transactions/<int:transaction_pk>/workflows/create/', views.TransactionWorkflowCreateView.as_view(), name='workflow_create'),
    
    # Task Management
    path('workflows/<int:workflow_pk>/tasks/create/', views.TransactionTaskCreateView.as_view(), name='task_create'),
    path('transactions/<int:transaction_pk>/tasks/create/', views.TransactionTaskCreateView.as_view(), name='task_create_for_transaction'),
    path('tasks/<int:task_pk>/update-status/', views.task_update_status, name='task_update_status'),
    
    # Monitoring and Reports
    path('monitoring/', views.transaction_monitoring, name='monitoring'),
    path('reports/', views.transaction_reports, name='reports'),
]