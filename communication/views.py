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
                conversations.append({
                    'user': user,
                    'latest_message': latest_message
                })
            except Message.DoesNotExist:
                continue

    # Sort conversations by the created_at of the latest message
    conversations.sort(key=lambda x: x['latest_message'].created_at, reverse=True)

    context = {
        'conversations': conversations,
    }
    return render(request, 'communication/messages.html', context)


@login_required
def message_detail_api(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Mark messages from the other user as read
    Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)
    
    messages = Message.objects.filter(
        (Q(sender=request.user, recipient=other_user) | Q(sender=other_user, recipient=request.user))
    ).order_by('created_at').values('sender__username', 'content', 'created_at')
    
    return JsonResponse(list(messages), safe=False)

@login_required
def send_message_api(request, user_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content')
            recipient = get_object_or_404(User, id=user_id)

            if content:
                message = Message.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    subject='Chat Message',  # Default subject for chat messages
                    content=content,
                    message_type='general'
                )
                return JsonResponse({'status': 'success', 'message': 'Message sent.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Content cannot be empty.'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

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

# Create your views here.
