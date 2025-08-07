from django.contrib import admin
from .models import DilisenseConfig, CapessoConfig, KYCProfile, KYCBusiness, KYCReport, Document

@admin.register(DilisenseConfig)
class DilisenseConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        # Only allow one configuration
        return not DilisenseConfig.objects.exists()

@admin.register(CapessoConfig)
class CapessoConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'base_url', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one active configuration
        return not CapessoConfig.objects.filter(is_active=True).exists()

@admin.register(KYCProfile)
class KYCProfileAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'full_name', 'email', 'nationality', 'created_at']
    list_filter = ['nationality', 'created_at', 'is_draft']
    search_fields = ['customer_id', 'full_name', 'email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(KYCBusiness)
class KYCBusinessAdmin(admin.ModelAdmin):
    list_display = ['business_id', 'business_name', 'business_type', 'industry_sector', 'created_at']
    list_filter = ['business_type', 'industry_sector', 'created_at', 'is_draft']
    search_fields = ['business_id', 'business_name', 'business_email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(KYCReport)
class KYCReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'report_type', 'decision', 'generated_at']
    list_filter = ['report_type', 'decision', 'generated_at']
    search_fields = ['report_id']
    readonly_fields = ['generated_at', 'updated_at']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'status', 'upload_date', 'verification_date']
    list_filter = ['document_type', 'status', 'upload_date']
    readonly_fields = ['upload_date', 'verification_date']
