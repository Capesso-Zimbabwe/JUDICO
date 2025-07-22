from django.contrib import admin
from .models import Message, Notification, Meeting

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

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'meeting_type', 'status', 'start_datetime', 'end_datetime', 'location')
    list_filter = ('meeting_type', 'status', 'start_datetime', 'send_reminders')
    search_fields = ('title', 'description', 'organizer__username', 'location')
    readonly_fields = ('created_at', 'updated_at', 'reminder_sent')
    filter_horizontal = ('participants',)
    ordering = ('start_datetime',)
    
    fieldsets = (
        ('Meeting Information', {
            'fields': ('title', 'description', 'meeting_type', 'status')
        }),
        ('Schedule', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Participants', {
            'fields': ('organizer', 'participants')
        }),
        ('Location & Platform', {
            'fields': ('location', 'meeting_link')
        }),
        ('Related Information', {
            'fields': ('related_client',)
        }),
        ('Notifications', {
            'fields': ('send_reminders', 'reminder_sent')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def send_reminders(self, request, queryset):
        count = 0
        for meeting in queryset:
            if meeting.is_upcoming() and not meeting.reminder_sent:
                meeting.send_reminder_notifications()
                count += 1
        self.message_user(request, f"Reminders sent for {count} meetings.")
    send_reminders.short_description = "Send reminder notifications"
    
    actions = ['send_reminders']
