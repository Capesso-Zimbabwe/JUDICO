from django.urls import path
from . import views

app_name = 'contract_management'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.contract_dashboard, name='contract_dashboard'),
    
    # Contract management
    path('', views.contract_list, name='contract_list'),
    path('list/', views.contract_list, name='contract_list'),
    path('create/', views.contract_create, name='contract_create'),
    path('<int:pk>/', views.contract_detail, name='contract_detail'),
    path('<int:pk>/edit/', views.contract_update, name='contract_update'),
    path('<int:pk>/delete/', views.contract_delete, name='contract_delete'),
    
    # Signature management
    path('<int:contract_pk>/add-signature/', views.add_signature_request, name='add_signature_request'),
    path('sign/<int:signature_id>/<str:verification_code>/', views.contract_sign, name='contract_sign'),
    
    # Template management
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    
    # Amendment management
    path('<int:contract_pk>/add-amendment/', views.add_amendment, name='add_amendment'),
    
    # API endpoints
    path('api/<int:pk>/update-status/', views.update_contract_status, name='update_contract_status'),
    path('api/statistics/', views.contract_statistics, name='contract_statistics'),
]