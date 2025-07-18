from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth.models import User

from .models import Task
from client_management.models import Client
from .forms import TaskForm
from django.utils import timezone
import json

# Helper function to check if user is staff or lawyer
def is_staff_or_lawyer(user):
    return user.is_staff or hasattr(user, 'lawyer_profile')

# Helper function to get common task data for all views
def get_task_data():
    # Base queryset with select_related for better performance
    tasks = Task.objects.select_related('client', 'assigned_to', 'created_by')
    
    # Calculate task counts for different statuses
    pending_tasks = Task.objects.filter(status='pending').count()
    in_progress_tasks = Task.objects.filter(status='in_progress').count()
    completed_tasks = Task.objects.filter(status='completed').count()
    
    return {
        'tasks': tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
    }

@login_required
@user_passes_test(is_staff_or_lawyer)
def task_list(request):
    status_filter = request.GET.get('status')
    
    # Get common task data
    context = get_task_data()
    
    # Apply status filter if provided
    if status_filter and status_filter in dict(Task.STATUS_CHOICES).keys():
        context['tasks'] = context['tasks'].filter(status=status_filter)
    
    context['status'] = status_filter
    return render(request, 'task_management/task_list.html', context)

@login_required
@user_passes_test(is_staff_or_lawyer)
def task_detail(request, pk):
    # Use get_object_or_404 for better error handling
    task = get_object_or_404(Task.objects.select_related('client', 'assigned_to', 'created_by'), pk=pk)
    
    # Get common task data
    context = get_task_data()
    context['task'] = task
    
    return render(request, 'task_management/task_detail.html', context)

@login_required
@user_passes_test(is_staff_or_lawyer)
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created successfully!')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm()
    
    # Get common task data
    context = get_task_data()
    context['form'] = form
    
    return render(request, 'task_management/task_form.html', context)

@login_required
@user_passes_test(is_staff_or_lawyer)
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    
    # Get common task data
    context = get_task_data()
    context['form'] = form
    
    return render(request, 'task_management/task_form.html', context)

@login_required
@user_passes_test(is_staff_or_lawyer)
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('task_list')
    
    # Get common task data
    context = get_task_data()
    context['task'] = task
    
    return render(request, 'task_management/task_confirm_delete.html', context)

@login_required
@user_passes_test(is_staff_or_lawyer)
def task_dashboard(request):
    # Get common task data
    context = get_task_data()
    
    # Get task counts by status
    task_status_counts = {
        status_name: Task.objects.filter(status=status_code).count() 
        for status_code, status_name in Task.STATUS_CHOICES
    }
    
    # Get task counts by priority
    task_priority_counts = {
        priority_name: Task.objects.filter(priority=priority_code).count() 
        for priority_code, priority_name in Task.PRIORITY_CHOICES
    }
    
    # Get top clients by task count (limit to top 5)
    top_clients = Client.objects.annotate(
        task_count=Count('tasks')
    ).filter(task_count__gt=0).order_by('-task_count')[:5]
    
    # Get top lawyers by assigned tasks (limit to top 5)
    top_lawyers = User.objects.filter(
        lawyer_profile__isnull=False
    ).annotate(
        task_count=Count('assigned_tasks')
    ).filter(task_count__gt=0).order_by('-task_count')[:5]
    
    # Get recent tasks (limit to 10)
    recent_tasks = Task.objects.select_related('client', 'assigned_to').order_by('-created_at')[:10]
    
    # Add additional context for dashboard
    context.update({
        'total_tasks': sum(task_status_counts.values()),
        'task_status_counts': task_status_counts,
        'task_priority_counts': task_priority_counts,
        'top_clients': top_clients,
        'top_lawyers': top_lawyers,
        'recent_tasks': recent_tasks,
        'low_priority_tasks': task_priority_counts.get('Low', 0),
        'medium_priority_tasks': task_priority_counts.get('Medium', 0),
        'high_priority_tasks': task_priority_counts.get('High', 0),
        'urgent_priority_tasks': task_priority_counts.get('Urgent', 0),
        'on_hold_tasks': task_status_counts.get('On Hold', 0),
        'client_labels': json.dumps([client.name for client in top_clients]),
        'client_tasks_data': json.dumps([client.task_count for client in top_clients]),
        'lawyer_labels': json.dumps([lawyer.get_full_name() or lawyer.username for lawyer in top_lawyers]),
        'lawyer_tasks_data': json.dumps([lawyer.task_count for lawyer in top_lawyers]),
    })
    
    return render(request, 'task_management/task_dashboard.html', context)
