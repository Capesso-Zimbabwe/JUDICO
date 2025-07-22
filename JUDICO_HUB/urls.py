from django.urls import path, include
from admin_portal.views import home
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import admin
from JUDICO_HUB import settings
# from django.contrib.admin. import
urlpatterns = [
    path('', login_required(home), name='home'),
    path('auth/', include('authentication.urls')),
    path('admin-portal/', include('admin_portal.urls', namespace='admin_portal')),
    path('lawyer/', include('lawyer_portal.urls', namespace='lawyer_portal')),
    path('client-portal/', include('client_portal.urls', namespace='client_portal')),
    path('task/', include('task_management.urls')),
    path('finance/', include('finance_management.urls')),
    path('hr/', include('hr_management.urls', namespace='hr_management')),
    path('transaction/', include('transaction_support.urls', namespace='transaction_support')),
    path('documents/', include('document_repository.urls', namespace='document_repository')),
    path('document/', lambda request: redirect('/documents/')),
    path('governance/', include('governance.urls', namespace='governance')),
    path('compliance/', include('compliance.urls', namespace='compliance')),
    path('kyc/', include('kyc_app.urls', namespace='kyc_app')),
    path('communication/', include('communication.urls', namespace='communication')),
    path('client/', include('client_management.urls', namespace='client_management')),


    # admin 
   path('admin/', admin.site.urls),
]


# if settings.DEBUG:
#     urlpatterns += [
#         # path('__debug__/', include('debug_toolbar.urls')),
#         path(settings.MEDIA_URL, settings.MEDIA_ROOT),
#         path(settings.STATIC_URL, settings.STATIC_ROOT)
#     ]