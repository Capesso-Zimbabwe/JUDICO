from django.db import models
from django.contrib.auth.models import User
from client_management.models import Client
from lawyer_portal.models import LawyerProfile

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
