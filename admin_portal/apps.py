from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class AdminPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_portal'


# Rename this to make it clear this is the main config for the app
class AdminPortalAdminConfig(AdminConfig):
    default_site = 'admin_portal.admin.CustomAdminSite'
