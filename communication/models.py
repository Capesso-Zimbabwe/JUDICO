from django.db import models
from django.contrib.auth.models import User
from client_management.models import Client
from lawyer_portal.models import LawyerProfile
from django.utils import timezone
from datetime import timedelta

class Message(models.Model):
    MESSAGE_TYPES = [
        ('general', 'General'),
        ('case_update', 'Case Update'),
        ('document_request', 'Document Request'),
        ('appointment', 'Appointment'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='general')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Optional: Link to client or case
    related_client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.subject}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.status = 'read'
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('document', 'Document Update'),
        ('appointment', 'Appointment Reminder'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    content = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"

class Meeting(models.Model):
    MEETING_TYPES = [
        ('consultation', 'Client Consultation'),
        ('case_review', 'Case Review'),
        ('court_hearing', 'Court Hearing'),
        ('deposition', 'Deposition'),
        ('team_meeting', 'Team Meeting'),
        ('client_meeting', 'Client Meeting'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, default='consultation')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    
    # Date and time
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    # Participants
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comm_organized_meetings')
    participants = models.ManyToManyField(User, related_name='comm_meeting_participants', blank=True)
    
    # Location/Platform
    location = models.CharField(max_length=300, blank=True, help_text="Physical location or meeting platform")
    meeting_link = models.URLField(blank=True, help_text="Video conference link")
    
    # Related entities
    related_client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    
    # Notifications
    send_reminders = models.BooleanField(default=True)
    reminder_sent = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_datetime']
    
    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"
    
    def is_upcoming(self):
        return self.start_datetime > timezone.now()
    
    def is_today(self):
        today = timezone.now().date()
        return self.start_datetime.date() == today
    
    def duration_minutes(self):
        return int((self.end_datetime - self.start_datetime).total_seconds() / 60)
    
    def send_reminder_notifications(self):
        """Send reminder notifications to all participants"""
        if not self.send_reminders or self.reminder_sent:
            return
        
        # Send notifications to all participants
        for participant in self.participants.all():
            Notification.objects.create(
                user=participant,
                title=f"Meeting Reminder: {self.title}",
                content=f"You have a meeting scheduled for {self.start_datetime.strftime('%B %d, %Y at %I:%M %p')}. Location: {self.location or 'TBD'}",
                notification_type='appointment'
            )
        
        self.reminder_sent = True
        self.save()
