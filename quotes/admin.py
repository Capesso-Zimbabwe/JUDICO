from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Quote


class QuoteResource(resources.ModelResource):
    class Meta:
        model = Quote
        fields = ('id', 'text', 'author', 'display_date', 'is_active', 'created_at')
        export_order = ('id', 'text', 'author', 'display_date', 'is_active', 'created_at')
        import_id_fields = ('id',)
        
    def before_import_row(self, row, **kwargs):
        """Process each row before import"""
        # If no display_date is provided, set a default
        if not row.get('display_date'):
            from datetime import datetime, timedelta
            import random
            today = datetime.now().date()
            random_days = random.randint(0, 365)
            row['display_date'] = today + timedelta(days=random_days)
        
        # If no author is provided, set to 'Unknown'
        if not row.get('author'):
            row['author'] = 'Unknown'
            
        # Set is_active to True if not specified
        if row.get('is_active') is None:
            row['is_active'] = True


class QuoteAdmin(ImportExportModelAdmin):
    resource_class = QuoteResource
    list_display = ('text_preview', 'author', 'display_date', 'is_active')
    list_filter = ('is_active', 'display_date', 'created_at')
    search_fields = ('text', 'author')
    date_hierarchy = 'created_at'
    list_editable = ('is_active',)
    ordering = ('-created_at',)
    
    # Import/Export settings
    import_template_name = 'admin/import_export/import.html'
    export_template_name = 'admin/import_export/export.html'
    
    def text_preview(self, obj):
        """Return a preview of the quote text"""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    
    text_preview.short_description = 'Quote'
