from django.contrib import admin
from .models import LawyerProfile, LawyerDocument
from admin_portal.admin import custom_admin_site

class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'years_of_experience', 'is_available')
    list_filter = ('specialization', 'is_available')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')

class LawyerDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lawyer', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title', 'lawyer__user__username')

# Register with the custom admin site
custom_admin_site.register(LawyerProfile, LawyerProfileAdmin)
custom_admin_site.register(LawyerDocument, LawyerDocumentAdmin)
