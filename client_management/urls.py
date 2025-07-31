from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'client_management'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='client_management:client_dashboard'), name='index'),
    # path('clients/', views.client_list, name='client_list'),

    path('clients/', views.ClientListView.as_view(), name='client_list'),

    path('clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    # path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/', views.ClientDetailsView.as_view(), name='client_detail'),

    path('clients/<int:pk>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),


    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('clients/<int:pk>/upload-document/', views.ClientDocumentCreateView.as_view(), name='upload_document'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    
    # Case Management URLs
    path('cases/', views.CaseListView.as_view(), name='case_list'),
    path('cases/create/', views.CaseCreateView.as_view(), name='case_create'),
    path('cases/<int:pk>/', views.CaseDetailsView.as_view(), name='case_detail'),
    path('cases/<int:pk>/update/', views.CaseUpdateView.as_view(), name='case_update'),
    path('cases/<int:case_id>/delete/', views.case_delete, name='case_delete'),
    path('cases/dashboard/', views.case_dashboard, name='case_dashboard'),
    
    # Case Update URLs
    path('cases/<int:pk>/add-update/', views.CaseUpdateCreateView.as_view(), name='case_add_update'),
    
    # Case Document URLs
    path('cases/<int:pk>/upload-document/', views.CaseDocumentCreateView.as_view(), name='case_upload_document'),
    path('case-documents/<int:document_id>/delete/', views.delete_case_document, name='delete_case_document'),
]