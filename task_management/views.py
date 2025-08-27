from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Task
from client_management.models import Client
from .forms import TaskForm, TaskFilterForm
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
    on_hold_tasks = Task.objects.filter(status='on_hold').count()
    
    return {
        'tasks': tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'on_hold_tasks': on_hold_tasks,
    }

@login_required
@user_passes_test(is_staff_or_lawyer)
def task_list(request):
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '')
    
    # Get common task data
    context = get_task_data()
    tasks_list = context['tasks']
    
    # Apply status filter if provided
    if status_filter and status_filter in dict(Task.STATUS_CHOICES).keys():
        tasks_list = tasks_list.filter(status=status_filter)
    
    # Apply search filter if provided
    if search_query:
        tasks_list = tasks_list.filter(
            Q(title__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(assigned_to__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(tasks_list, 10)  # Show 10 tasks per page
    page = request.GET.get('page')
    
    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        tasks = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        tasks = paginator.page(paginator.num_pages)
    
    # Add search form to context
    initial = {}
    if search_query:
        initial['search'] = search_query
    
    context['search_form'] = TaskFilterForm(initial=initial)
    context['status'] = status_filter
    context['tasks'] = tasks
    context['page_obj'] = tasks  # For paginator template
    
    return render(request, 'task_management/task_list.html', context)

@login_required
@user_passes_test(is_staff_or_lawyer)
def task_detail(request, pk):
    # Use get_object_or_404 for better error handling
    task = get_object_or_404(Task.objects.select_related('client', 'assigned_to', 'created_by'), pk=pk)
    
    # Get common task data
    context = get_task_data()
    context['task'] = task
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'task_management/task_detail_modal.html', context)
    
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
            return redirect('task_list')
    else:
        form = TaskForm()
    
    # Get common task data
    context = get_task_data()
    context['form'] = form
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'task_management/task_form_modal.html', context)
    
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
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    
    # Get common task data
    context = get_task_data()
    context['form'] = form
    context['task'] = task
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'task_management/task_form_modal.html', context)
    
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
    
    # Get monthly task creation data
    from django.db.models import Q
    from datetime import datetime, timedelta
    import calendar
    
    current_year = datetime.now().year
    monthly_data = []
    for month in range(1, 13):
        month_tasks = Task.objects.filter(
            created_at__year=current_year,
            created_at__month=month
        ).count()
        monthly_data.append(month_tasks)
    
    # Get overdue and due date analysis
    today = datetime.now().date()
    overdue_tasks = Task.objects.filter(due_date__lt=today, status__in=['pending', 'in_progress']).count()
    due_today_tasks = Task.objects.filter(due_date=today, status__in=['pending', 'in_progress']).count()
    due_this_week_tasks = Task.objects.filter(
        due_date__gte=today,
        due_date__lte=today + timedelta(days=7),
        status__in=['pending', 'in_progress']
    ).count()
    due_next_week_tasks = Task.objects.filter(
        due_date__gt=today + timedelta(days=7),
        due_date__lte=today + timedelta(days=14),
        status__in=['pending', 'in_progress']
    ).count()
    future_tasks = Task.objects.filter(
        due_date__gt=today + timedelta(days=14),
        status__in=['pending', 'in_progress']
    ).count()
    
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
        'monthly_task_data': json.dumps(monthly_data),
        'overdue_tasks': overdue_tasks,
        'due_today_tasks': due_today_tasks,
        'due_this_week_tasks': due_this_week_tasks,
        'due_next_week_tasks': due_next_week_tasks,
        'future_tasks': future_tasks,
    })
    
    return render(request, 'task_management/task_dashboard.html', context)
