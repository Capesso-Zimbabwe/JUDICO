from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Requirement, Audit
from .forms import RequirementForm, AuditForm

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
    return render(request, 'compliance/reports.html')

# Create your views here.
