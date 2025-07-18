from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Screening, Entity, Alert, Transaction, WatchList, WatchListEntry, ScreeningResult
from .forms import ScreeningForm, EntityForm
import json

def aml_dashboard(request):
    # Get dashboard statistics
    active_screenings = Screening.objects.filter(status__in=['pending', 'in_progress']).count()
    high_risk_alerts = Alert.objects.filter(priority='high', status__in=['new', 'under_review']).count()
    pending_reviews = Screening.objects.filter(status='flagged').count()
    
    # Calculate compliance score (simplified)
    total_screenings = Screening.objects.count()
    completed_screenings = Screening.objects.filter(status__in=['completed', 'cleared']).count()
    compliance_score = round((completed_screenings / total_screenings * 100) if total_screenings > 0 else 100)
    
    context = {
        'active_screenings': active_screenings,
        'high_risk_alerts': high_risk_alerts,
        'pending_reviews': pending_reviews,
        'compliance_score': compliance_score,
    }
    return render(request, 'aml_system/dashboard.html', context)

def screening_list(request):
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    risk_filter = request.GET.get('risk', 'all')
    
    # Base queryset
    screenings = Screening.objects.select_related('entity', 'initiated_by').all()
    
    # Apply filters
    if search_query:
        screenings = screenings.filter(
            Q(entity__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    if status_filter != 'all':
        screenings = screenings.filter(status=status_filter)
    
    if risk_filter != 'all':
        screenings = screenings.filter(risk_level=risk_filter)
    
    # Order by creation date (newest first)
    screenings = screenings.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(screenings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'screenings': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'risk_filter': risk_filter,
        'status_choices': Screening.STATUS_CHOICES,
        'risk_choices': Screening.RISK_LEVELS,
    }
    return render(request, 'aml_system/screening.html', context)

@login_required
def screening_create(request):
    if request.method == 'POST':
        form = ScreeningForm(request.POST)
        if form.is_valid():
            screening = form.save(commit=False)
            screening.initiated_by = request.user
            screening.save()
            messages.success(request, 'Screening created successfully.')
            return redirect('aml_system:screening_detail', pk=screening.pk)
    else:
        form = ScreeningForm()
    
    context = {
        'form': form,
        'title': 'Create New Screening'
    }
    return render(request, 'aml_system/screening_form.html', context)

@login_required
def screening_detail(request, pk):
    screening = get_object_or_404(Screening, pk=pk)
    results = screening.results.select_related('watch_list_entry__watch_list').all()
    
    context = {
        'screening': screening,
        'results': results,
    }
    return render(request, 'aml_system/screening_detail.html', context)

@login_required
def screening_update(request, pk):
    screening = get_object_or_404(Screening, pk=pk)
    
    if request.method == 'POST':
        form = ScreeningForm(request.POST, instance=screening)
        if form.is_valid():
            form.save()
            messages.success(request, 'Screening updated successfully.')
            return redirect('aml_system:screening_detail', pk=screening.pk)
    else:
        form = ScreeningForm(instance=screening)
    
    context = {
        'form': form,
        'screening': screening,
        'title': f'Update Screening #{screening.id}'
    }
    return render(request, 'aml_system/screening_form.html', context)

@login_required
def entity_create(request):
    if request.method == 'POST':
        form = EntityForm(request.POST)
        if form.is_valid():
            entity = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'entity_id': entity.id,
                    'entity_name': entity.name
                })
            messages.success(request, 'Entity created successfully.')
            return redirect('aml_system:screening_create')
    else:
        form = EntityForm()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'aml_system/entity_form_modal.html', {'form': form})
    
    context = {
        'form': form,
        'title': 'Create New Entity'
    }
    return render(request, 'aml_system/entity_form.html', context)

def monitoring_list(request):
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    # Base queryset
    alerts = Alert.objects.select_related('entity', 'assigned_to').all()
    
    # Apply search filter
    if search_query:
        alerts = alerts.filter(
            Q(alert_id__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(entity__name__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        alerts = alerts.filter(status=status_filter)
    
    # Apply priority filter
    if priority_filter:
        alerts = alerts.filter(priority=priority_filter)
    
    # Order by creation date (newest first)
    alerts = alerts.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(alerts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'alerts': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': Alert.STATUS_CHOICES,
        'priority_choices': Alert.PRIORITY_LEVELS,
    }
    return render(request, 'aml_system/monitoring.html', context)

@login_required
def alert_detail(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    
    context = {
        'alert': alert,
    }
    return render(request, 'aml_system/alert_detail.html', context)

@login_required
def alert_escalate(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    
    if request.method == 'POST':
        alert.status = 'escalated'
        alert.priority = 'high'
        alert.assigned_to = request.user
        alert.updated_at = timezone.now()
        alert.save()
        
        messages.success(request, f'Alert {alert.alert_id} has been escalated successfully.')
        return redirect('aml_system:alert_detail', pk=alert.pk)
    
    context = {
        'alert': alert,
    }
    return render(request, 'aml_system/alert_escalate.html', context)

def reports_list(request):
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', 'all')
    date_range_filter = request.GET.get('date_range', 'all')
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset for reports (using Alert model as proxy for reports)
    reports = Alert.objects.select_related('entity', 'assigned_to').all()
    
    # Apply search filter
    if search_query:
        reports = reports.filter(
            Q(alert_id__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply type filter (using alert_type as report_type)
    if type_filter != 'all':
        if type_filter == 'screening':
            reports = reports.filter(alert_type='screening_alert')
        elif type_filter == 'monitoring':
            reports = reports.filter(alert_type='monitoring_alert')
        elif type_filter == 'compliance':
            reports = reports.filter(alert_type='compliance_alert')
    
    # Apply date range filter
    if date_range_filter != 'all':
        now = timezone.now()
        if date_range_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range_filter == 'week':
            start_date = now - timedelta(days=7)
        elif date_range_filter == 'month':
            start_date = now - timedelta(days=30)
        elif date_range_filter == 'quarter':
            start_date = now - timedelta(days=90)
        elif date_range_filter == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = None
        
        if start_date:
            reports = reports.filter(created_at__gte=start_date)
    
    # Apply status filter
    if status_filter != 'all':
        # Map report statuses to alert statuses
        status_mapping = {
            'generated': 'new',
            'reviewed': 'under_review',
            'approved': 'resolved',
            'archived': 'closed'
        }
        mapped_status = status_mapping.get(status_filter, status_filter)
        reports = reports.filter(status=mapped_status)
    
    # Order by creation date (newest first)
    reports = reports.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reports, 12)  # 12 reports per page for grid layout
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reports': page_obj,
        'search_query': search_query,
        'type_filter': type_filter,
        'date_range_filter': date_range_filter,
        'status_filter': status_filter,
    }
    return render(request, 'aml_system/reports.html', context)

@login_required
def report_create(request):
    if request.method == 'POST':
        # Handle report creation logic here
        # For now, create a basic alert as a report placeholder
        alert = Alert.objects.create(
            alert_id=f"RPT-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            alert_type='compliance_alert',
            subject=request.POST.get('title', 'Generated Report'),
            description=request.POST.get('description', 'Auto-generated compliance report'),
            status='new',
            priority='medium',
            entity_id=request.POST.get('entity_id') if request.POST.get('entity_id') else None,
            assigned_to=request.user
        )
        messages.success(request, 'Report generated successfully.')
        return redirect('aml_system:report_detail', pk=alert.pk)
    
    # Get entities for the form
    entities = Entity.objects.all()
    
    context = {
        'entities': entities,
        'title': 'Generate New Report'
    }
    return render(request, 'aml_system/report_create.html', context)

@login_required
def report_detail(request, pk):
    report = get_object_or_404(Alert, pk=pk)
    
    context = {
        'report': report,
    }
    return render(request, 'aml_system/report_detail.html', context)

@login_required
def report_download(request, pk):
    from django.http import HttpResponse
    import json
    
    report = get_object_or_404(Alert, pk=pk)
    
    # Generate a simple JSON report for download
    report_data = {
        'report_id': report.alert_id,
        'title': report.subject,
        'description': report.description,
        'status': report.status,
        'priority': report.priority,
        'created_at': report.created_at.isoformat(),
        'created_by': report.assigned_to.username if report.assigned_to else 'System',
        'entity': report.entity.name if report.entity else None,
    }
    
    response = HttpResponse(
        json.dumps(report_data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{report.alert_id}_report.json"'
    
    return response
