from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from communication.models import Notification
from datetime import datetime, timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Populate sample notifications for testing'

    def handle(self, *args, **options):
        # Clear existing notifications
        Notification.objects.all().delete()
        self.stdout.write('Cleared existing notifications')
        
        # Get all users
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return
        
        notification_types = ['message', 'document', 'appointment', 'system']
        
        sample_notifications = [
            {
                'title': 'New Message Received',
                'content': 'You have received a new message from John Doe regarding your case.',
                'notification_type': 'message'
            },
            {
                'title': 'Document Updated',
                'content': 'The contract document has been updated and requires your review.',
                'notification_type': 'document'
            },
            {
                'title': 'Meeting Reminder',
                'content': 'You have a consultation meeting scheduled for tomorrow at 2:00 PM.',
                'notification_type': 'appointment'
            },
            {
                'title': 'System Maintenance',
                'content': 'The system will undergo maintenance tonight from 11 PM to 1 AM.',
                'notification_type': 'system'
            },
            {
                'title': 'Court Hearing Scheduled',
                'content': 'A court hearing has been scheduled for next week. Please check your calendar.',
                'notification_type': 'appointment'
            },
            {
                'title': 'New Client Message',
                'content': 'Sarah Johnson has sent you a message about her case status.',
                'notification_type': 'message'
            },
            {
                'title': 'Document Approval Required',
                'content': 'The legal brief requires your approval before submission.',
                'notification_type': 'document'
            },
            {
                'title': 'Payment Received',
                'content': 'Payment has been received for invoice #12345.',
                'notification_type': 'system'
            },
            {
                'title': 'Deposition Scheduled',
                'content': 'A deposition has been scheduled for Friday at 10:00 AM.',
                'notification_type': 'appointment'
            },
            {
                'title': 'Case Update',
                'content': 'There has been an update to the Johnson vs. Smith case.',
                'notification_type': 'system'
            }
        ]
        
        created_count = 0
        
        for user in users:
            # Create 3-7 notifications per user
            num_notifications = random.randint(3, 7)
            selected_notifications = random.sample(sample_notifications, min(num_notifications, len(sample_notifications)))
            
            for i, notif_data in enumerate(selected_notifications):
                # Create notifications with varying read status and timestamps
                is_read = random.choice([True, False]) if i > 0 else False  # First notification is always unread
                
                # Create timestamps from last 7 days
                days_ago = random.randint(0, 7)
                hours_ago = random.randint(0, 23)
                created_at = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
                
                notification = Notification.objects.create(
                    user=user,
                    title=notif_data['title'],
                    content=notif_data['content'],
                    notification_type=notif_data['notification_type'],
                    is_read=is_read
                )
                
                # Manually set the created_at timestamp
                notification.created_at = created_at
                notification.save()
                
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample notifications')
        )
        
        # Show summary
        for user in users:
            total = Notification.objects.filter(user=user).count()
            unread = Notification.objects.filter(user=user, is_read=False).count()
            self.stdout.write(f'{user.username}: {total} total, {unread} unread')