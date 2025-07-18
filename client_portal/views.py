from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import ClientProfile
from task_management.models import Task
from client_management.models import ClientDocument

def is_client(user):
    return hasattr(user, 'client_profile')

@login_required
def client_check(request):
    if is_client(request.user):
        return redirect('client_portal:dashboard')
    else:
        messages.error(request, 'You need to be registered as a client to access this portal.')
        return redirect('home')

@login_required
def dashboard(request):
    if not is_client(request.user):
        return redirect('client_portal:client_check')
    
    client_profile = request.user.client_profile
    client = client_profile.client
    
    # Get tasks assigned to this client
    tasks = Task.objects.filter(client=client).order_by('-created_at')
    
    # Task statistics
    task_counts = {
        'total': tasks.count(),
        'pending': tasks.filter(status='pending').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'completed': tasks.filter(status='completed').count(),
        'on_hold': tasks.filter(status='on_hold').count(),
    }
    
    # Recent tasks (last 5)
    recent_tasks = tasks[:5]
    
    # Recent documents
    recent_documents = ClientDocument.objects.filter(client=client).order_by('-uploaded_at')[:5]
    
    context = {
        'client': client,
        'task_counts': task_counts,
        'recent_tasks': recent_tasks,
        'recent_documents': recent_documents,
    }
    
    return render(request, 'client_portal/dashboard.html', context)

@login_required
def tasks(request):
    if not is_client(request.user):
        return redirect('client_portal:client_check')
    
    client_profile = request.user.client_profile
    client = client_profile.client
    
    # Get status filter
    status_filter = request.GET.get('status')
    
    # Get tasks for this client
    tasks = Task.objects.filter(client=client).order_by('-created_at')
    
    # Apply status filter if provided
    if status_filter and status_filter in dict(Task.STATUS_CHOICES).keys():
        tasks = tasks.filter(status=status_filter)
    
    # Task statistics
    task_counts = {
        'total': Task.objects.filter(client=client).count(),
        'pending': Task.objects.filter(client=client, status='pending').count(),
        'in_progress': Task.objects.filter(client=client, status='in_progress').count(),
        'completed': Task.objects.filter(client=client, status='completed').count(),
        'on_hold': Task.objects.filter(client=client, status='on_hold').count(),
    }
    
    context = {
        'client': client,
        'tasks': tasks,
        'task_counts': task_counts,
        'status_filter': status_filter,
        'status_choices': Task.STATUS_CHOICES,
    }
    
    return render(request, 'client_portal/tasks.html', context)

@login_required
def task_detail(request, task_id):
    if not is_client(request.user):
        return redirect('client_portal:client_check')
    
    client_profile = request.user.client_profile
    client = client_profile.client
    
    # Get task and ensure it belongs to this client
    task = get_object_or_404(Task, id=task_id, client=client)
    
    context = {
        'client': client,
        'task': task,
    }
    
    return render(request, 'client_portal/task_detail.html', context)

@login_required
def documents(request):
    if not is_client(request.user):
        return redirect('client_portal:client_check')
    
    client_profile = request.user.client_profile
    client = client_profile.client
    
    documents = ClientDocument.objects.filter(client=client).order_by('-uploaded_at')
    
    context = {
        'client': client,
        'documents': documents,
    }
    
    return render(request, 'client_portal/documents.html', context)

@login_required
def projects(request):
    if not is_client(request.user):
        return redirect('client_portal:client_check')
    
    client_profile = request.user.client_profile
    client = client_profile.client
    
    # Get projects for this client (using tasks as projects for now)
    projects = Task.objects.filter(client=client).order_by('-created_at')
    
    context = {
        'client': client,
        'projects': projects,
    }
    
    return render(request, 'client_portal/projects.html', context)

@login_required
def communications(request):
    if not is_client(request.user):
        return redirect('client_portal:client_check')
    
    client_profile = request.user.client_profile
    client = client_profile.client
    
    # Import Message model
    from communication.models import Message, Notification
    
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
    
    # Get recent messages (last 10)
    recent_messages = Message.objects.filter(
        models.Q(sender=request.user) | models.Q(recipient=request.user)
    ).order_by('-created_at')[:10]
    
    # Get notifications
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
        'client': client,
        'recent_messages': recent_messages,
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'notifications': notifications,
        'message_stats': message_stats,
    }
    
    return render(request, 'client_portal/communications.html', context)

@login_required
def profile(request):
    if not is_client(request.user):
        return redirect('client_portal:client_check')
    
    client_profile = request.user.client_profile
    client = client_profile.client
    
    context = {
        'client': client,
    }
    
    return render(request, 'client_portal/profile.html', context)
