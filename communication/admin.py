from django.contrib import admin
from .models import Message, Notification, Meeting, MessageAttachment

@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'message', 'filesize', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['filename', 'message__subject']
    readonly_fields = ['filesize', 'uploaded_at']
    
    def filesize_formatted(self, obj):
        return f"{obj.filesize} bytes"
    filesize_formatted.short_description = 'File Size'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'message_type', 'status', 'is_read', 'created_at']
    list_filter = ['message_type', 'status', 'is_read', 'created_at']
    search_fields = ['sender__username', 'recipient__username', 'subject', 'content']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'recipient', 'subject', 'content', 'message_type')
        }),
        ('Status', {
            'fields': ('status', 'is_read', 'read_at')
        }),
        ('Related', {
            'fields': ('related_client',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'content']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'meeting_type', 'status', 'organizer', 'start_datetime', 'end_datetime']
    list_filter = ['meeting_type', 'status', 'start_datetime']
    search_fields = ['title', 'description', 'organizer__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_datetime'
    
    fieldsets = (
        ('Meeting Details', {
            'fields': ('title', 'description', 'meeting_type', 'status')
        }),
        ('Schedule', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Participants', {
            'fields': ('organizer', 'participants')
        }),
        ('Location', {
            'fields': ('location', 'meeting_link')
        }),
        ('Related', {
            'fields': ('related_client',),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('send_reminders', 'reminder_sent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
