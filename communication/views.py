from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Message, Notification, Meeting
from django.contrib.auth.models import User
import json

@login_required
def communication_dashboard(request):
    # Get upcoming meetings for the current user
    upcoming_meetings = Meeting.objects.filter(
        participants=request.user,
        start_datetime__gte=timezone.now()
    ).order_by('start_datetime')[:5]
    
    # Get today's meetings
    today = timezone.now().date()
    today_meetings = Meeting.objects.filter(
        participants=request.user,
        start_datetime__date=today
    ).order_by('start_datetime')
    
    # Get meeting data for calendar
    calendar_meetings = Meeting.objects.filter(
        participants=request.user,
        start_datetime__gte=timezone.now() - timedelta(days=30),
        start_datetime__lte=timezone.now() + timedelta(days=60)
    )
    
    # Format meetings for calendar
    calendar_events = []
    for meeting in calendar_meetings:
        calendar_events.append({
            'id': meeting.id,
            'title': meeting.title,
            'start': meeting.start_datetime.isoformat(),
            'end': meeting.end_datetime.isoformat(),
            'description': meeting.description,
            'location': meeting.location,
            'type': meeting.meeting_type,
            'status': meeting.status,
            'organizer': meeting.organizer.get_full_name() or meeting.organizer.username,
            'participants': [p.get_full_name() or p.username for p in meeting.participants.all()]
        })
    
    context = {
        'upcoming_meetings': upcoming_meetings,
        'today_meetings': today_meetings,
        'calendar_events': json.dumps(calendar_events),
    }
    
    return render(request, 'communication/dashboard.html', context)

from django.db.models import Q, Max

@login_required
def message_list(request):
    """Enhanced message list view with conversation data"""
    # Get all users the current user has had a conversation with
    sent_to = Message.objects.filter(sender=request.user).values_list('recipient', flat=True)
    received_from = Message.objects.filter(recipient=request.user).values_list('sender', flat=True)
    
    user_ids = set(list(sent_to) + list(received_from))
    
    conversations = []
    if user_ids:
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            try:
                latest_message = Message.objects.filter(
                    (Q(sender=request.user, recipient=user) | Q(sender=user, recipient=request.user))
                ).latest('created_at')
                
                # Count unread messages from this user
                unread_count = Message.objects.filter(
                    sender=user,
                    recipient=request.user,
                    is_read=False
                ).count()
                
                conversations.append({
                    'user': user,
                    'latest_message': latest_message,
                    'unread_count': unread_count
                })
            except Message.DoesNotExist:
                continue

    # Sort conversations by the created_at of the latest message
    conversations.sort(key=lambda x: x['latest_message'].created_at, reverse=True)

    context = {
        'conversations': conversations,
        'selected_user': None,
        'selected_user_id': None,
        'messages': []
    }
    
    # Check if a specific user is selected
    selected_user_id = request.GET.get('user')
    if selected_user_id:
        try:
            selected_user = User.objects.get(id=selected_user_id)
            context['selected_user'] = selected_user
            context['selected_user_id'] = selected_user_id
            
            # Get messages for this conversation
            messages = Message.objects.filter(
                (Q(sender=request.user, recipient=selected_user) | Q(sender=selected_user, recipient=request.user))
            ).order_by('created_at')
            context['messages'] = messages
            
            # Mark messages as read
            Message.objects.filter(sender=selected_user, recipient=request.user, is_read=False).update(is_read=True)
            
        except User.DoesNotExist:
            pass
    
    return render(request, 'communication/messages.html', context)


@login_required
def message_detail_api(request, user_id):
    """Get detailed messages between current user and another user"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Mark messages from the other user as read
    Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)
    
    messages = Message.objects.filter(
        (Q(sender=request.user, recipient=other_user) | Q(sender=other_user, recipient=request.user))
    ).order_by('created_at')
    
    # Format messages for the frontend
    message_data = []
    for message in messages:
        message_data.append({
            'id': message.id,
            'sender_id': message.sender.id,
            'sender_name': message.sender.get_full_name() or message.sender.username,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'is_read': message.is_read,
            'attachments': list(message.attachments.all().values('filename', 'filesize'))
        })
    
    return JsonResponse({
        'success': True,
        'messages': message_data,
        'other_user': {
            'id': other_user.id,
            'name': other_user.get_full_name() or other_user.username,
            'is_lawyer': hasattr(other_user, 'lawyerprofile')
        }
    })

@login_required
def send_message_api(request):
    """Send a message with optional file attachments"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        attachment = request.FILES.get('attachment')
        
        if not recipient_id or not content:
            return JsonResponse({'success': False, 'message': 'Missing required fields'})
        
        try:
            recipient = User.objects.get(id=recipient_id)
            
            # Create the message
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject='New Message',
                content=content
            )
            
            # Handle file attachment if provided
            if attachment:
                # You can extend this to handle multiple file types
                # For now, we'll store basic file information
                message.attachments.add(attachment)
            
            # Mark as read for the sender
            message.mark_as_read()
            
            return JsonResponse({'success': True, 'message_id': message.id})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Recipient not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def notification_list(request):
    # Get filter parameter
    filter_type = request.GET.get('filter', 'all')
    
    # Base queryset for user's notifications
    notifications = Notification.objects.filter(user=request.user)
    
    # Apply filters
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'important':
        notifications = notifications.filter(notification_type='appointment')
    
    # Order by creation date (newest first)
    notifications = notifications.order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications,
        'filter': filter_type,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'communication/notifications.html', context)

def communication_settings(request):
    return render(request, 'communication/settings.html')

@login_required
def meeting_list(request):
    meetings = Meeting.objects.filter(
        participants=request.user
    ).order_by('start_datetime')
    
    context = {
        'meetings': meetings,
    }
    return render(request, 'communication/meeting_list.html', context)

@login_required
def meeting_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        meeting_type = request.POST.get('meeting_type')
        start_datetime = request.POST.get('start_datetime')
        end_datetime = request.POST.get('end_datetime')
        location = request.POST.get('location', '')
        meeting_link = request.POST.get('meeting_link', '')
        participant_ids = request.POST.getlist('participants')
        
        try:
            # Parse datetime strings
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            
            # Create meeting
            meeting = Meeting.objects.create(
                title=title,
                description=description,
                meeting_type=meeting_type,
                start_datetime=start_dt,
                end_datetime=end_dt,
                location=location,
                meeting_link=meeting_link,
                organizer=request.user
            )
            
            # Add participants
            if participant_ids:
                participants = User.objects.filter(id__in=participant_ids)
                meeting.participants.set(participants)
            
            # Add organizer as participant
            meeting.participants.add(request.user)
            
            # Send notifications to participants
            for participant in meeting.participants.all():
                if participant != request.user:  # Don't notify organizer
                    Notification.objects.create(
                        user=participant,
                        title=f"New Meeting: {meeting.title}",
                        content=f"You have been invited to a meeting scheduled for {meeting.start_datetime.strftime('%B %d, %Y at %I:%M %p')}.",
                        notification_type='appointment'
                    )
            
            messages.success(request, 'Meeting created successfully!')
            return redirect('communication:meeting_list')
            
        except Exception as e:
            messages.error(request, f'Error creating meeting: {str(e)}')
    
    # Get all users for participant selection
    users = User.objects.all().order_by('first_name', 'last_name', 'username')
    
    context = {
        'users': users,
        'meeting_types': Meeting.MEETING_TYPES,
    }
    return render(request, 'communication/meeting_create.html', context)

@login_required
def meeting_detail(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, participants=request.user)
    
    context = {
        'meeting': meeting,
    }
    return render(request, 'communication/meeting_detail.html', context)

@login_required
def calendar_api(request):
    """API endpoint for calendar events"""
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    if start_date and end_date:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        meetings = Meeting.objects.filter(
            participants=request.user,
            start_datetime__gte=start_dt,
            start_datetime__lte=end_dt
        )
    else:
        meetings = Meeting.objects.filter(
            participants=request.user,
            start_datetime__gte=timezone.now() - timedelta(days=30),
            start_datetime__lte=timezone.now() + timedelta(days=60)
        )
    
    events = []
    for meeting in meetings:
        color = {
            'consultation': '#3B82F6',
            'case_review': '#10B981',
            'court_hearing': '#EF4444',
            'deposition': '#F59E0B',
            'team_meeting': '#8B5CF6',
            'client_meeting': '#06B6D4',
        }.get(meeting.meeting_type, '#6B7280')
        
        events.append({
            'id': meeting.id,
            'title': meeting.title,
            'start': meeting.start_datetime.isoformat(),
            'end': meeting.end_datetime.isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'description': meeting.description,
                'location': meeting.location,
                'type': meeting.get_meeting_type_display(),
                'status': meeting.get_status_display(),
                'organizer': meeting.organizer.get_full_name() or meeting.organizer.username,
                'participants': [p.get_full_name() or p.username for p in meeting.participants.all()]
            }
        })
    
    return JsonResponse(events, safe=False)

@login_required
def notification_count_api(request):
    """API endpoint to get unread notification count"""
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    if request.method == 'POST':
        try:
            notification = get_object_or_404(Notification, id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    if request.method == 'POST':
        try:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def clear_all_notifications(request):
    """Clear all notifications for the current user"""
    if request.method == 'POST':
        try:
            Notification.objects.filter(user=request.user).delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def new_conversation(request):
    """View to select a user to start a new conversation with"""
    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id).order_by('first_name', 'last_name', 'username')
    
    context = {
        'users': users,
    }
    return render(request, 'communication/new_conversation.html', context)

@login_required
def get_users_by_type(request, user_type):
    """Get users by type (client or lawyer) for new conversations"""
    from client_management.models import Client
    from lawyer_portal.models import LawyerProfile
    
    if user_type == 'client':
        users = Client.objects.all()
        user_data = [{
            'id': client.user.id,
            'name': client.user.get_full_name() or client.user.username,
            'type': 'client'
        } for client in users if client.user]
    elif user_type == 'lawyer':
        users = LawyerProfile.objects.all()
        user_data = [{
            'id': lawyer.user.id,
            'name': lawyer.user.get_full_name() or lawyer.user.username,
            'type': 'lawyer',
            'specialization': lawyer.specialization
        } for lawyer in users if lawyer.user]
    else:
        user_data = []
    
    return JsonResponse({'users': user_data})

# Create your views here.
