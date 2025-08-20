from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Transaction, TransactionEntity, EntityOwnershipHistory,
    TransactionDocument, DueDiligenceCategory, TransactionWorkflow,
    TransactionTask, TransactionAuditLog, TransactionReport,
    ContractReassignment
)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'title', 'transaction_type', 'status', 'priority',
        'primary_client', 'lead_lawyer', 'transaction_value', 'target_closing_date',
        'created_at', 'is_active'
    ]
    list_filter = [
        'transaction_type', 'status', 'priority', 'is_confidential',
        'regulatory_approvals_required', 'created_at', 'target_closing_date'
    ]
    search_fields = ['code', 'title', 'description', 'primary_client__name']
    readonly_fields = ['code', 'created_at', 'updated_at', 'is_active', 'days_to_closing']
    filter_horizontal = ['team_members', 'related_cases', 'related_contracts']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'title', 'description', 'transaction_type', 'status', 'priority')
        }),
        ('Financial Details', {
            'fields': ('transaction_value', 'currency')
        }),
        ('Dates', {
            'fields': ('target_closing_date', 'actual_closing_date', 'created_at', 'updated_at', 'days_to_closing')
        }),
        ('Team & Relationships', {
            'fields': ('primary_client', 'lead_lawyer', 'team_members', 'created_by')
        }),
        ('Related Items', {
            'fields': ('related_cases', 'related_contracts')
        }),
        ('Settings', {
            'fields': ('is_confidential', 'regulatory_approvals_required', 'notes')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'primary_client', 'lead_lawyer', 'created_by'
        ).prefetch_related('team_members')

@admin.register(TransactionEntity)
class TransactionEntityAdmin(admin.ModelAdmin):
    list_display = [
        'transaction', 'client', 'role', 'ownership_percentage', 'get_transaction_status'
    ]
    list_filter = ['role', 'transaction__status', 'transaction__transaction_type']
    search_fields = ['transaction__code', 'transaction__title', 'client__name']
    autocomplete_fields = ['transaction', 'client']
    
    def get_transaction_status(self, obj):
        return obj.transaction.get_status_display()
    get_transaction_status.short_description = 'Transaction Status'
    get_transaction_status.admin_order_field = 'transaction__status'

@admin.register(EntityOwnershipHistory)
class EntityOwnershipHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'entity', 'previous_ownership', 'new_ownership', 'change_date', 'recorded_by'
    ]
    list_filter = ['change_date', 'entity__role']
    search_fields = ['entity__client__name', 'change_reason']
    readonly_fields = ['change_date']
    autocomplete_fields = ['entity', 'recorded_by']

@admin.register(TransactionDocument)
class TransactionDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'transaction', 'document_type', 'version', 'access_level',
        'uploaded_by', 'uploaded_at', 'is_reviewed', 'file_size_display'
    ]
    list_filter = [
        'document_type', 'access_level', 'is_reviewed', 'uploaded_at',
        'transaction__status', 'transaction__transaction_type'
    ]
    search_fields = ['title', 'description', 'transaction__code', 'transaction__title']
    readonly_fields = ['uploaded_at', 'last_accessed', 'file_size', 'file_hash', 'version']
    autocomplete_fields = ['transaction', 'uploaded_by', 'reviewed_by', 'parent_document']
    filter_horizontal = ['due_diligence_categories']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'description', 'document_type', 'access_level')
        }),
        ('File Details', {
            'fields': ('document_file', 'file_size', 'file_hash', 'version', 'parent_document')
        }),
        ('Transaction & Categories', {
            'fields': ('transaction', 'due_diligence_categories')
        }),
        ('Review Status', {
            'fields': ('is_reviewed', 'reviewed_by', 'reviewed_at')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at', 'last_accessed')
        })
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"
    file_size_display.short_description = 'File Size'
    file_size_display.admin_order_field = 'file_size'

@admin.register(DueDiligenceCategory)
class DueDiligenceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'is_active', 'subcategory_count']
    list_filter = ['is_active', 'parent_category']
    search_fields = ['name', 'description']
    autocomplete_fields = ['parent_category']
    
    def subcategory_count(self, obj):
        return obj.subcategories.count()
    subcategory_count.short_description = 'Subcategories'

@admin.register(TransactionWorkflow)
class TransactionWorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'transaction_type', 'is_template', 'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['transaction_type', 'is_template', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    autocomplete_fields = ['created_by']

@admin.register(TransactionTask)
class TransactionTaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'transaction', 'task_type', 'status', 'priority',
        'assigned_to', 'due_date', 'progress_percentage', 'is_overdue'
    ]
    list_filter = [
        'task_type', 'status', 'priority', 'due_date',
        'transaction__status', 'transaction__transaction_type'
    ]
    search_fields = ['title', 'description', 'transaction__code', 'transaction__title']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'is_overdue']
    autocomplete_fields = ['transaction', 'workflow', 'assigned_to', 'created_by']
    filter_horizontal = ['depends_on']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'task_type', 'status', 'priority')
        }),
        ('Assignment', {
            'fields': ('transaction', 'workflow', 'assigned_to', 'created_by')
        }),
        ('Dates & Progress', {
            'fields': ('due_date', 'completed_at', 'created_at', 'updated_at', 'progress_percentage')
        }),
        ('Time Tracking', {
            'fields': ('estimated_hours', 'actual_hours')
        }),
        ('Dependencies', {
            'fields': ('depends_on',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'transaction', 'assigned_to', 'created_by'
        )

class TransactionAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'transaction', 'user', 'action_type', 'object_type',
        'description_short', 'ip_address'
    ]
    list_filter = [
        'action_type', 'object_type', 'timestamp',
        'transaction__status', 'transaction__transaction_type'
    ]
    search_fields = ['description', 'transaction__code', 'user__username']
    readonly_fields = [
        'timestamp', 'transaction', 'user', 'action_type', 'object_type',
        'object_id', 'description', 'ip_address', 'user_agent', 'session_id',
        'old_values', 'new_values'
    ]
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False  # Audit logs should not be manually created
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted

admin.site.register(TransactionAuditLog, TransactionAuditLogAdmin)

@admin.register(TransactionReport)
class TransactionReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'transaction', 'report_type', 'generated_by',
        'generated_at', 'is_confidential', 'has_file'
    ]
    list_filter = [
        'report_type', 'is_confidential', 'generated_at',
        'transaction__status', 'transaction__transaction_type'
    ]
    search_fields = ['title', 'description', 'transaction__code', 'transaction__title']
    readonly_fields = ['generated_at']
    autocomplete_fields = ['transaction', 'generated_by']
    filter_horizontal = ['shared_with']
    
    def has_file(self, obj):
        return bool(obj.report_file)
    has_file.boolean = True
    has_file.short_description = 'Has File'

@admin.register(ContractReassignment)
class ContractReassignmentAdmin(admin.ModelAdmin):
    list_display = [
        'contract', 'transaction', 'original_client', 'new_client',
        'reassignment_date', 'approved_by', 'is_active'
    ]
    list_filter = [
        'is_active', 'reassignment_date',
        'transaction__status', 'transaction__transaction_type'
    ]
    search_fields = [
        'contract__title', 'transaction__code', 'original_client__name',
        'new_client__name', 'reason'
    ]
    readonly_fields = ['reassignment_date']
    autocomplete_fields = [
        'transaction', 'contract', 'original_client', 'new_client',
        'original_lawyer', 'new_lawyer', 'approved_by'
    ]
    
    fieldsets = (
        ('Reassignment Details', {
            'fields': ('transaction', 'contract', 'reason', 'reassignment_date')
        }),
        ('Original Assignment', {
            'fields': ('original_client', 'original_lawyer')
        }),
        ('New Assignment', {
            'fields': ('new_client', 'new_lawyer')
        }),
        ('Approval & Status', {
            'fields': ('approved_by', 'is_active', 'notes')
        })
    )

# Customize admin site header and title
admin.site.site_header = "JUDICO Legal Management System"
admin.site.site_title = "JUDICO Admin"
admin.site.index_title = "Transaction Support Administration"
