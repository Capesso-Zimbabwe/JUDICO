from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'client_management'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='client_management:client_dashboard'), name='index'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/update/', views.client_update, name='client_update'),
    path('clients/<int:client_id>/delete/', views.client_delete, name='client_delete'),
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('clients/<int:client_id>/upload-document/', views.upload_document, name='upload_document'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
]