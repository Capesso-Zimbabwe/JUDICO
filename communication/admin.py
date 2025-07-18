from django.contrib import admin
from .models import Message, Notification

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'message_type', 'status', 'is_read', 'created_at')
    list_filter = ('message_type', 'status', 'is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'subject', 'content')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)
    
    def mark_as_read(self, request, queryset):
        for message in queryset:
            message.mark_as_read()
        self.message_user(request, f"{queryset.count()} messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    actions = ['mark_as_read']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'content')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
