from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Client, ClientDocument


class ClientResource(resources.ModelResource):
    class Meta:
        model = Client
        fields = ('id', 'name', 'contact_person', 'email', 'phone', 'address', 'case_type', 'registration_date', 'is_active', 'assigned_lawyer', 'lawyer')
        export_order = ('id', 'name', 'contact_person', 'email', 'phone', 'address', 'case_type', 'registration_date', 'is_active', 'assigned_lawyer', 'lawyer')


class ClientDocumentResource(resources.ModelResource):
    class Meta:
        model = ClientDocument
        fields = ('id', 'client', 'title', 'document', 'uploaded_at')
        export_order = ('id', 'client', 'title', 'document', 'uploaded_at')


@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    resource_class = ClientResource
    list_display = ('name', 'contact_person', 'email', 'phone', 'case_type', 'registration_date', 'is_active', 'assigned_lawyer')
    list_filter = ('case_type', 'is_active', 'registration_date', 'assigned_lawyer')
    search_fields = ('name', 'contact_person', 'email', 'phone')
    list_editable = ('is_active',)
    date_hierarchy = 'registration_date'
    ordering = ('-registration_date',)


@admin.register(ClientDocument)
class ClientDocumentAdmin(ImportExportModelAdmin):
    resource_class = ClientDocumentResource
    list_display = ('client', 'title', 'uploaded_at')
    list_filter = ('uploaded_at', 'client')
    search_fields = ('client__name', 'title')
    date_hierarchy = 'uploaded_at'
    ordering = ('-uploaded_at',)
