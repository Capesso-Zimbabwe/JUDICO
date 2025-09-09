from django.apps import AppConfig


class HrManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hr_management'

    def ready(self):
        # Import signal handlers
        from . import signals  # noqa: F401