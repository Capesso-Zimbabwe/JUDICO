from django.contrib import admin
from .models import Requirement, Audit

@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'status', 'due_date', 'created_by', 'created_at']
    list_filter = ['category', 'status', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'audit_type', 'status', 'priority', 'scheduled_date', 'auditor', 'created_by', 'created_at']
    list_filter = ['audit_type', 'status', 'priority', 'scheduled_date', 'created_at']
    search_fields = ['title', 'auditor', 'description', 'findings']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
