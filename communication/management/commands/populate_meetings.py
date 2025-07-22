from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from communication.models import Meeting
import random

class Command(BaseCommand):
    help = 'Populate sample meeting data for testing'
    
    def handle(self, *args, **options):
        # Get all users
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return
        
        # Clear existing meetings
        Meeting.objects.all().delete()
        
        # Sample meeting data
        meeting_types = ['consultation', 'case_review', 'court_hearing', 'deposition', 'team_meeting', 'client_meeting']
        statuses = ['scheduled', 'in_progress', 'completed', 'cancelled', 'rescheduled']
        
        sample_meetings = [
            {
                'title': 'Client Consultation - Smith Case',
                'description': 'Initial consultation with new client regarding personal injury case.',
                'meeting_type': 'consultation',
                'status': 'scheduled',
                'location': 'Conference Room A',
                'meeting_link': 'https://zoom.us/j/123456789',
            },
            {
                'title': 'Case Review - Johnson vs. ABC Corp',
                'description': 'Weekly case review meeting to discuss progress and next steps.',
                'meeting_type': 'case_review',
                'status': 'scheduled',
                'location': 'Main Conference Room',
            },
            {
                'title': 'Court Hearing - Municipal Court',
                'description': 'Preliminary hearing for traffic violation case.',
                'meeting_type': 'court_hearing',
                'status': 'scheduled',
                'location': 'Municipal Court, Room 201',
            },
            {
                'title': 'Team Meeting - Weekly Sync',
                'description': 'Weekly team synchronization meeting to discuss ongoing cases.',
                'meeting_type': 'team_meeting',
                'status': 'scheduled',
                'location': 'Virtual',
                'meeting_link': 'https://teams.microsoft.com/l/meetup-join/19%3ameeting',
            },
            {
                'title': 'Deposition - Witness Interview',
                'description': 'Deposition of key witness in the Henderson case.',
                'meeting_type': 'deposition',
                'status': 'scheduled',
                'location': 'Law Office Conference Room',
            },
            {
                'title': 'Client Meeting - Contract Review',
                'description': 'Meeting with client to review and finalize contract terms.',
                'meeting_type': 'client_meeting',
                'status': 'completed',
                'location': 'Client Office',
            },
            {
                'title': 'Emergency Consultation',
                'description': 'Urgent consultation regarding criminal charges.',
                'meeting_type': 'consultation',
                'status': 'scheduled',
                'location': 'Virtual',
                'meeting_link': 'https://zoom.us/j/987654321',
            },
            {
                'title': 'Case Strategy Meeting',
                'description': 'Strategic planning session for upcoming trial.',
                'meeting_type': 'case_review',
                'status': 'scheduled',
                'location': 'Conference Room B',
            },
        ]
        
        # Create meetings with different dates
        now = timezone.now()
        created_count = 0
        
        for i, meeting_data in enumerate(sample_meetings):
            # Create meetings spread across the next 30 days
            days_offset = i * 3  # Space meetings 3 days apart
            hours_offset = random.randint(9, 17)  # Random hour between 9 AM and 5 PM
            minutes_offset = random.choice([0, 15, 30, 45])  # Quarter-hour intervals
            
            start_datetime = now + timedelta(days=days_offset, hours=hours_offset-now.hour, minutes=minutes_offset-now.minute)
            end_datetime = start_datetime + timedelta(hours=1)  # 1-hour meetings
            
            # Select random organizer and participants
            organizer = random.choice(users)
            participants = random.sample(users, min(random.randint(2, 4), len(users)))
            
            meeting = Meeting.objects.create(
                title=meeting_data['title'],
                description=meeting_data['description'],
                meeting_type=meeting_data['meeting_type'],
                status=meeting_data['status'],
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                location=meeting_data.get('location', ''),
                meeting_link=meeting_data.get('meeting_link', ''),
                organizer=organizer,
                send_reminders=True,
            )
            
            # Add participants
            meeting.participants.set(participants)
            
            created_count += 1
            
        # Create some meetings for today
        today_meetings = [
            {
                'title': "Today's Client Call",
                'description': 'Important client call scheduled for today.',
                'meeting_type': 'consultation',
                'status': 'scheduled',
                'location': 'Virtual',
                'meeting_link': 'https://zoom.us/j/111222333',
                'hour': 10,
            },
            {
                'title': 'Team Standup',
                'description': 'Daily team standup meeting.',
                'meeting_type': 'team_meeting',
                'status': 'scheduled',
                'location': 'Conference Room A',
                'hour': 14,
            },
        ]
        
        for meeting_data in today_meetings:
            start_datetime = now.replace(hour=meeting_data['hour'], minute=0, second=0, microsecond=0)
            end_datetime = start_datetime + timedelta(hours=1)
            
            organizer = random.choice(users)
            participants = random.sample(users, min(random.randint(2, 3), len(users)))
            
            meeting = Meeting.objects.create(
                title=meeting_data['title'],
                description=meeting_data['description'],
                meeting_type=meeting_data['meeting_type'],
                status=meeting_data['status'],
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                location=meeting_data.get('location', ''),
                meeting_link=meeting_data.get('meeting_link', ''),
                organizer=organizer,
                send_reminders=True,
            )
            
            meeting.participants.set(participants)
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample meetings')
        )
        
        # Show some statistics
        total_meetings = Meeting.objects.count()
        upcoming_meetings = Meeting.objects.filter(start_datetime__gte=now).count()
        today_meetings = Meeting.objects.filter(start_datetime__date=now.date()).count()
        
        self.stdout.write(f'Total meetings: {total_meetings}')
        self.stdout.write(f'Upcoming meetings: {upcoming_meetings}')
        self.stdout.write(f"Today's meetings: {today_meetings}")