from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Requirement, Audit
from .forms import RequirementForm, AuditForm
from django.utils import timezone
from datetime import timedelta

@login_required
def compliance_dashboard(request):
    total_requirements = Requirement.objects.count()
    context = {
        'total_requirements': total_requirements,
        'total_audits': 0,
        'total_reports': 0,
    }
    return render(request, 'compliance/dashboard.html', context)

@login_required
def regulatory_calendar(request):
    """Regulatory calendar showing requirements and audits on a timeline with filters."""
    # Filters
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    period = request.GET.get('period', '60')  # days forward

    # Requirements within window
    today = timezone.now().date()
    end_date = today + timedelta(days=int(period))
    reqs = Requirement.objects.filter(due_date__gte=today, due_date__lte=end_date)
    if category:
        reqs = reqs.filter(category=category)
    if status:
        reqs = reqs.filter(status=status)

    # Audits within window
    audits = Audit.objects.filter(scheduled_date__gte=today, scheduled_date__lte=end_date)

    # Build events for calendar JS
    events = []
    for r in reqs:
        events.append({
            'id': f'req-{r.id}',
            'title': r.title,
            'start': r.due_date.isoformat(),
            'end': r.due_date.isoformat(),
            'type': 'requirement',
            'category': r.category,
            'status': r.status,
            'priority': r.priority or '',
        })
    for a in audits:
        events.append({
            'id': f'aud-{a.id}',
            'title': a.title,
            'start': a.scheduled_date.isoformat(),
            'end': (a.completion_date or a.scheduled_date).isoformat(),
            'type': 'audit',
            'status': a.status,
            'priority': a.priority,
        })

    import json
    context = {
        'events_json': json.dumps(events),
        'category_choices': Requirement.CATEGORY_CHOICES,
        'status_choices': Requirement.STATUS_CHOICES,
        'selected_category': category,
        'selected_status': status,
        'selected_period': period,
    }
    return render(request, 'compliance/regulatory_calendar.html', context)

@login_required
def requirements_list(request):
    requirements = Requirement.objects.all()
    context = {
        'requirements': requirements,
    }
    return render(request, 'compliance/requirements.html', context)

@login_required
def create_requirement(request):
    if request.method == 'POST':
        form = RequirementForm(request.POST)
        if form.is_valid():
            requirement = form.save(commit=False)
            requirement.created_by = request.user
            requirement.save()
            messages.success(request, 'Requirement created successfully!')
            return redirect('compliance:requirements')
        else:
            messages.error(request, 'Please correct the errors below.')
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = RequirementForm()
    
    context = {
        'form': form,
    }
    return render(request, 'compliance/requirements.html', context)

@login_required
def audits_list(request):
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    # Start with all audits
    audits = Audit.objects.all()
    
    # Apply search filter
    if search_query:
        audits = audits.filter(
            Q(title__icontains=search_query) |
            Q(auditor__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply type filter
    if type_filter:
        audits = audits.filter(audit_type=type_filter)
    
    # Apply status filter
    if status_filter:
        audits = audits.filter(status=status_filter)
    
    # Apply priority filter
    if priority_filter:
        audits = audits.filter(priority=priority_filter)
    
    # Order by creation date (newest first)
    audits = audits.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(audits, 10)  # Show 10 audits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get choices for filters
    type_choices = Audit.TYPE_CHOICES
    status_choices = Audit.STATUS_CHOICES
    priority_choices = Audit.PRIORITY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'audits': page_obj,
        'search_query': search_query,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'type_choices': type_choices,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'form': AuditForm(),
    }
    return render(request, 'compliance/audits.html', context)

@login_required
def create_audit(request):
    if request.method == 'POST':
        form = AuditForm(request.POST)
        if form.is_valid():
            audit = form.save(commit=False)
            audit.created_by = request.user
            audit.save()
            messages.success(request, 'Audit scheduled successfully!')
            return redirect('compliance:audits')
        else:
            messages.error(request, 'Please correct the errors below.')
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = AuditForm()
    
    context = {
        'form': form,
    }
    return render(request, 'compliance/audits.html', context)

@login_required
def update_audit(request, audit_id):
    audit = get_object_or_404(Audit, id=audit_id)
    
    if request.method == 'POST':
        form = AuditForm(request.POST, instance=audit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Audit updated successfully!')
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def audit_details(request, audit_id):
    audit = get_object_or_404(Audit, id=audit_id)
    
    if request.method == 'GET':
        data = {
            'id': audit.id,
            'title': audit.title,
            'audit_type': audit.get_audit_type_display(),
            'status': audit.get_status_display(),
            'priority': audit.get_priority_display(),
            'scheduled_date': audit.scheduled_date.strftime('%Y-%m-%d') if audit.scheduled_date else '',
            'completion_date': audit.completion_date.strftime('%Y-%m-%d') if audit.completion_date else '',
            'auditor': audit.auditor,
            'description': audit.description,
            'findings': audit.findings,
            'created_by': audit.created_by.get_full_name() or audit.created_by.username,
            'created_at': audit.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': audit.updated_at.strftime('%Y-%m-%d %H:%M'),
        }
        return JsonResponse(data)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def compliance_reports(request):
    """Compliance reports page with filters and CSV export similar to finance reports UI."""
    # Filters
    report_type = request.GET.get('report_type', '')  # requirements_summary, audits_schedule
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    period = int(request.GET.get('period', '30'))  # days ahead
    export = request.GET.get('export', '')

    today = timezone.now().date()
    end_date = today + timedelta(days=period)

    # Build dataset based on report type
    rows = []
    if report_type in ('', 'requirements_summary'):
        qs = Requirement.objects.filter(due_date__gte=today, due_date__lte=end_date)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if category_filter:
            qs = qs.filter(category=category_filter)
        for r in qs.order_by('due_date'):
            rows.append({
                'name': r.title,
                'type': 'Requirement',
                'period': r.due_date.strftime('%Y-%m-%d'),
                'format': 'Record',
                'status': r.status,
                'generated_by': r.created_by.get_full_name() or r.created_by.username,
            })

    if report_type == 'audits_schedule':
        qs = Audit.objects.filter(scheduled_date__gte=today, scheduled_date__lte=end_date)
        if status_filter:
            qs = qs.filter(status=status_filter)
        for a in qs.order_by('scheduled_date'):
            rows.append({
                'name': a.title,
                'type': f'Audit · {a.get_audit_type_display()}',
                'period': a.scheduled_date.strftime('%Y-%m-%d'),
                'format': 'Record',
                'status': a.status,
                'generated_by': a.created_by.get_full_name() or a.created_by.username,
            })

    # CSV export
    if export == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="compliance_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Report Name', 'Type', 'Period', 'Format', 'Status', 'Generated By'])
        for row in rows:
            writer.writerow([row['name'], row['type'], row['period'], row['format'], row['status'], row['generated_by']])
        return response

    # Pagination
    from django.core.paginator import Paginator
    page_number = request.GET.get('page')
    paginator = Paginator(rows, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'rows': page_obj,
        'page_obj': page_obj,
        'report_type': report_type,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'period': str(period),
        'category_choices': Requirement.CATEGORY_CHOICES,
        'status_choices': Requirement.STATUS_CHOICES,
    }
    return render(request, 'compliance/reports.html', context)

# Create your views here.
