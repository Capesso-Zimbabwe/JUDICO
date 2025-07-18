from django.contrib import admin
from .models import ClientProfile
from admin_portal.admin import custom_admin_site

class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'client', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'client__name')
    raw_id_fields = ('user', 'client')

# Register with both default admin and custom admin
admin.site.register(ClientProfile, ClientProfileAdmin)
custom_admin_site.register(ClientProfile, ClientProfileAdmin)
