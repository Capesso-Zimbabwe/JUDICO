from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'document_repository'

urlpatterns = [
    path('', lambda request: redirect('document_repository:dashboard'), name='document_root'),
    path('dashboard/', views.document_dashboard, name='dashboard'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<int:document_id>/edit/', views.document_update, name='document_update'),
    path('categories/', views.category_list, name='category_list'),
    path('search/', views.document_search, name='document_search'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
]