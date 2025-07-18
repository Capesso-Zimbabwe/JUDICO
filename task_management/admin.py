from django.contrib import admin
from .models import Task
from admin_portal.admin import custom_admin_site

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'assigned_to', 'status', 'priority', 'due_date')
    list_filter = ('status', 'priority', 'due_date')
    search_fields = ('title', 'description', 'client__name', 'assigned_to__username')
    date_hierarchy = 'due_date'

# Register with the custom admin site
custom_admin_site.register(Task, TaskAdmin)

# Register your models here.
