from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import LawyerProfile, LawyerDocument
from client_management.models import Client
from task_management.models import Task
from communication.models import Message, Notification

def is_lawyer(user):
    return hasattr(user, 'lawyer_profile')

@login_required
def lawyer_check(request):
    if is_lawyer(request.user):
        return redirect('lawyer_portal:dashboard')
    else:
        return render(request, 'lawyer_portal/not_lawyer.html')

@login_required
def dashboard(request):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    from finance_management.models import Invoice, Payment
    from governance.models import Meeting
    from django.db.models import Sum, Q
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    lawyer = request.user.lawyer_profile
    documents = LawyerDocument.objects.filter(lawyer=lawyer).order_by('-uploaded_at')[:5]
    
    # Get lawyer's clients
    lawyer_clients = Client.objects.filter(lawyer=lawyer)
    client_count = lawyer_clients.count()
    active_clients = lawyer_clients.filter(is_active=True).count()
    
    # Get task statistics for the lawyer
    lawyer_tasks = Task.objects.filter(assigned_to=request.user)
    task_counts = {
        'total': lawyer_tasks.count(),
        'pending': lawyer_tasks.filter(status='pending').count(),
        'in_progress': lawyer_tasks.filter(status='in_progress').count(),
        'completed': lawyer_tasks.filter(status='completed').count(),
        'on_hold': lawyer_tasks.filter(status='on_hold').count(),
    }
    
    # Get recent tasks (last 5)
    recent_tasks = lawyer_tasks.order_by('-created_at')[:5]
    
    # Get billing/financial metrics
    lawyer_invoices = Invoice.objects.filter(client__lawyer=lawyer)
    total_revenue = lawyer_invoices.filter(status='PAID').aggregate(Sum('total'))['total__sum'] or 0
    pending_invoices = lawyer_invoices.filter(status='SENT').count()
    overdue_invoices = lawyer_invoices.filter(status='OVERDUE').count()
    
    # Get communication metrics
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    total_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).count()
    
    # Get upcoming meetings/deadlines
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    upcoming_meetings = Meeting.objects.filter(
        attendees=request.user,
        date__date__gte=today,
        date__date__lte=next_week,
        status='scheduled'
    ).count()
    
    # Get urgent tasks (due within 3 days)
    urgent_tasks = lawyer_tasks.filter(
        due_date__lte=today + timedelta(days=3),
        status__in=['pending', 'in_progress']
    ).count()
    
    # Document statistics
    document_count = LawyerDocument.objects.filter(lawyer=lawyer).count()
    
    context = {
        'lawyer': lawyer,
        'documents': documents,
        'client_count': client_count,
        'active_clients': active_clients,
        'task_counts': task_counts,
        'recent_tasks': recent_tasks,
        'total_revenue': total_revenue,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'unread_messages': unread_messages,
        'total_messages': total_messages,
        'upcoming_meetings': upcoming_meetings,
        'urgent_tasks': urgent_tasks,
        'document_count': document_count,
        # Task counts for charts
        'task_pending_count': task_counts['pending'],
        'task_in_progress_count': task_counts['in_progress'],
        'task_completed_count': task_counts['completed'],
        'task_on_hold_count': task_counts['on_hold'],
    }
    
    return render(request, 'lawyer_portal/dashboard.html', context)

@login_required
def transactions(request):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    return render(request, 'lawyer_portal/transactions.html')

@login_required
def documents(request):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    lawyer = request.user.lawyer_profile
    documents = LawyerDocument.objects.filter(lawyer=lawyer).order_by('-uploaded_at')
    
    context = {
        'documents': documents,
    }
    
    return render(request, 'lawyer_portal/documents.html', context)

@login_required
def communications(request):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    # Get message querysets without ordering first to avoid slice issues
    received_messages_qs = Message.objects.filter(recipient=request.user)
    sent_messages_qs = Message.objects.filter(sender=request.user)
    
    # Get message statistics first (before applying ordering)
    unread_count = received_messages_qs.filter(is_read=False).count()
    total_received = received_messages_qs.count()
    total_sent = sent_messages_qs.count()
    
    # Now apply ordering for display
    received_messages = received_messages_qs.order_by('-created_at')
    sent_messages = sent_messages_qs.order_by('-created_at')
    
    # Get recent messages (both sent and received)
    recent_messages = Message.objects.filter(
        models.Q(sender=request.user) | models.Q(recipient=request.user)
    ).order_by('-created_at')[:10]
    
    # Get notifications for the lawyer
    notifications_qs = Notification.objects.filter(user=request.user)
    unread_notifications = notifications_qs.filter(is_read=False).count()
    notifications = notifications_qs.order_by('-created_at')[:5]
    
    # Message statistics
    message_stats = {
        'total_received': total_received,
        'total_sent': total_sent,
        'unread': unread_count,
        'unread_notifications': unread_notifications,
    }
    
    context = {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'recent_messages': recent_messages,
        'notifications': notifications,
        'message_stats': message_stats,
    }
    
    return render(request, 'lawyer_portal/communications.html', context)

@login_required
def clients(request):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    lawyer = request.user.lawyer_profile
    clients = Client.objects.filter(lawyer=lawyer)
    
    context = {
        'clients': clients,
    }
    
    return render(request, 'lawyer_portal/clients.html', context)
@login_required
def tasks(request):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    # Get all tasks assigned to the current lawyer
    lawyer_tasks = Task.objects.filter(assigned_to=request.user).order_by('-created_at')
    
    # Get task counts by status for the lawyer
    task_counts = {
        'pending': lawyer_tasks.filter(status='pending').count(),
        'in_progress': lawyer_tasks.filter(status='in_progress').count(),
        'completed': lawyer_tasks.filter(status='completed').count(),
        'on_hold': lawyer_tasks.filter(status='on_hold').count(),
    }
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter and status_filter in dict(Task.STATUS_CHOICES).keys():
        lawyer_tasks = lawyer_tasks.filter(status=status_filter)
    
    context = {
        'tasks': lawyer_tasks,
        'task_counts': task_counts,
        'status_filter': status_filter,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
    }
    
    return render(request, 'lawyer_portal/tasks.html', context)

@login_required
def task_detail(request, task_id):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    # Get the task and ensure it's assigned to the current lawyer
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    context = {
        'task': task,
        'status_choices': Task.STATUS_CHOICES,
    }
    
    return render(request, 'lawyer_portal/task_detail.html', context)

@login_required
def update_task_status(request, task_id):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    # Get the task and ensure it's assigned to the current lawyer
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES).keys():
            old_status = task.get_status_display()
            task.status = new_status
            task.save()
            messages.success(request, f'Task status updated from "{old_status}" to "{task.get_status_display()}"')
        else:
            messages.error(request, 'Invalid status selected')
    
    return redirect('lawyer_portal:task_detail', task_id=task_id)

@login_required
def create_lawyer_profile(request):
    # This would be a form view to create a lawyer profile
    # For now, just render a template
    return render(request, 'lawyer_portal/create_profile.html')

@login_required
def edit_lawyer_profile(request):
    if not is_lawyer(request.user):
        return redirect('lawyer_portal:lawyer_check')
    
    lawyer = request.user.lawyer_profile
    
    # This would typically include form handling logic
    # For now, just render a template with the current profile data
    context = {
        'lawyer': lawyer,
    }
    
    return render(request, 'lawyer_portal/edit_profile.html', context)
