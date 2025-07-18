from django.contrib import admin
from .models import Quote

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'author', 'display_date', 'is_active')
    list_filter = ('is_active', 'display_date')
    search_fields = ('text', 'author')
    date_hierarchy = 'created_at'
    
    def text_preview(self, obj):
        """Return a preview of the quote text"""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    
    text_preview.short_description = 'Quote'
