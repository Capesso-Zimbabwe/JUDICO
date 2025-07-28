from django.contrib import admin
from .models import Contract, ContractSignature, ContractTemplate, ContractAmendment

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'contract_type', 'status', 'assigned_lawyer', 'contract_value', 'start_date', 'end_date', 'created_at']
    list_filter = ['status', 'contract_type', 'created_at', 'start_date', 'end_date']
    search_fields = ['title', 'client__name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'signed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'contract_type', 'client', 'assigned_lawyer', 'created_by')
        }),
        ('Contract Details', {
            'fields': ('status', 'contract_value', 'start_date', 'end_date')
        }),
        ('Document', {
            'fields': ('contract_document',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_template')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'signed_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'assigned_lawyer', 'created_by')

@admin.register(ContractSignature)
class ContractSignatureAdmin(admin.ModelAdmin):
    list_display = ['signer_name', 'signer_email', 'contract', 'signature_type', 'status', 'signed_at', 'is_verified']
    list_filter = ['signature_type', 'status', 'is_verified', 'created_at']
    search_fields = ['signer_name', 'signer_email', 'contract__title']
    readonly_fields = ['created_at', 'signed_at', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Signer Information', {
            'fields': ('contract', 'signer_name', 'signer_email', 'signature_type')
        }),
        ('Signature Status', {
            'fields': ('status', 'signature_image', 'is_verified', 'verification_code')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'signed_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contract')

@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'contract_type', 'created_by', 'is_active', 'created_at']
    list_filter = ['contract_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'contract_type', 'created_by')
        }),
        ('Template Content', {
            'fields': ('template_content', 'template_file')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ContractAmendment)
class ContractAmendmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'contract', 'created_by', 'is_approved', 'approved_by', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['title', 'description', 'contract__title']
    readonly_fields = ['created_at', 'approved_at']
    
    fieldsets = (
        ('Amendment Information', {
            'fields': ('contract', 'title', 'description', 'created_by')
        }),
        ('Document', {
            'fields': ('amendment_document',)
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contract', 'created_by', 'approved_by')

# Inline admin for signatures in contract admin
class ContractSignatureInline(admin.TabularInline):
    model = ContractSignature
    extra = 0
    readonly_fields = ['signed_at', 'ip_address']
    fields = ['signer_name', 'signer_email', 'signature_type', 'status', 'signed_at']

# Inline admin for amendments in contract admin
class ContractAmendmentInline(admin.TabularInline):
    model = ContractAmendment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['title', 'is_approved', 'created_at']

# Update ContractAdmin to include inlines
ContractAdmin.inlines = [ContractSignatureInline, ContractAmendmentInline]
