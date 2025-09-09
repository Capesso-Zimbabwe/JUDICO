from django.contrib import admin
from django.contrib.auth.models import User, Group
from client_management.models import Client, ClientDocument
from quotes.models import Quote
from quotes.admin import QuoteAdmin
# Import models from other apps as needed

# Add this to the top of your existing admin.py file
from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    site_header = 'JUDICO Administration'
    site_title = 'JUDICO Admin Portal'
    index_title = 'JUDICO Management'

# Create an instance of the custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register your models with the custom admin site
custom_admin_site.register(User)
custom_admin_site.register(Group)

# Register Client and ClientDocument with the custom admin site
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'is_active', 'assigned_lawyer')
    list_filter = ('is_active', 'registration_date')
    search_fields = ('name', 'contact_person', 'email')

custom_admin_site.register(Client, ClientAdmin)

class ClientDocumentAdmin(admin.ModelAdmin):
    list_display = ('client', 'title', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title', 'client__name')

custom_admin_site.register(ClientDocument, ClientDocumentAdmin)

# Register Quotes with the custom admin site
custom_admin_site.register(Quote, QuoteAdmin)

# Register models from other apps as needed
