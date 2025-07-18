from django.contrib import admin
from .models import DocumentCategory, Document, DocumentAccess

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'document_count', 'created_at')
    list_filter = ('created_at', 'color')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def document_count(self, obj):
        return obj.document_count
    document_count.short_description = 'Documents'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'file_type', 'uploaded_by', 'uploaded_at', 'file_size_mb', 'access_count')
    list_filter = ('category', 'file_type', 'uploaded_at', 'is_active')
    search_fields = ('title', 'description', 'tags')
    readonly_fields = ('uploaded_at', 'updated_at', 'access_count', 'last_accessed', 'file_size_mb')
    list_per_page = 25
    
    def file_size_mb(self, obj):
        return f"{obj.file_size_mb} MB"
    file_size_mb.short_description = 'File Size'

@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'accessed_at', 'ip_address')
    list_filter = ('accessed_at',)
    search_fields = ('document__title', 'user__username')
    readonly_fields = ('accessed_at',)
    list_per_page = 50
