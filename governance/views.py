from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Policy, Meeting, Report
from .forms import PolicyForm, MeetingForm, ReportForm

@login_required
def dashboard(request):
    total_policies = Policy.objects.count()
    active_policies = Policy.objects.filter(status='active').count()
    draft_policies = Policy.objects.filter(status='draft').count()
    
    total_meetings = Meeting.objects.count()
    upcoming_meetings = Meeting.objects.filter(date__gte=timezone.now(), status='scheduled').count()
    
    context = {
        'total_policies': total_policies,
        'active_policies': active_policies,
        'draft_policies': draft_policies,
        'total_meetings': total_meetings,
        'upcoming_meetings': upcoming_meetings,
        'total_reports': 0,
        'recent_activities': 0,
    }
    return render(request, 'governance/dashboard.html', context)

@login_required
def policies(request):
    policies_list = Policy.objects.all()
    context = {
        'policies': policies_list
    }
    return render(request, 'governance/policies.html', context)

@login_required
def create_policy(request):
    if request.method == 'POST':
        form = PolicyForm(request.POST, request.FILES)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.created_by = request.user
            policy.updated_by = request.user
            policy.save()
            messages.success(request, 'Policy created successfully!')
            return redirect('governance:policies')
    else:
        form = PolicyForm()
    
    context = {
        'form': form,
        'title': 'Create New Policy'
    }
    return render(request, 'governance/policy_form.html', context)

@login_required
def edit_policy(request, policy_id):
    policy = get_object_or_404(Policy, id=policy_id)
    
    if request.method == 'POST':
        form = PolicyForm(request.POST, request.FILES, instance=policy)
        if form.is_valid():
            updated_policy = form.save(commit=False)
            updated_policy.updated_by = request.user
            updated_policy.save()
            messages.success(request, 'Policy updated successfully!')
            return redirect('governance:policies')
    else:
        form = PolicyForm(instance=policy)
    
    context = {
        'form': form,
        'policy': policy,
        'title': 'Edit Policy'
    }
    return render(request, 'governance/policy_form.html', context)

@login_required
def delete_policy(request, policy_id):
    policy = get_object_or_404(Policy, id=policy_id)
    
    if request.method == 'POST':
        policy.delete()
        messages.success(request, 'Policy deleted successfully!')
        return redirect('governance:policies')
    
    context = {
        'policy': policy
    }
    return render(request, 'governance/confirm_delete.html', context)

@login_required
def view_policy(request, policy_id):
    policy = get_object_or_404(Policy, id=policy_id)
    context = {
        'policy': policy
    }
    return render(request, 'governance/policy_detail.html', context)

@login_required
def meetings(request):
    now = timezone.now()
    upcoming_meetings = Meeting.objects.filter(
        date__gte=now,
        status='scheduled'
    ).order_by('date')[:5]
    
    recent_meetings = Meeting.objects.filter(
        date__lt=now
    ).order_by('-date')[:5]
    
    all_meetings = Meeting.objects.all().order_by('-date')
    
    context = {
        'upcoming_meetings': upcoming_meetings,
        'recent_meetings': recent_meetings,
        'all_meetings': all_meetings,
    }
    return render(request, 'governance/meetings.html', context)

@login_required
def create_meeting(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.organizer = request.user
            meeting.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Meeting created successfully!')
            return redirect('governance:meetings')
    else:
        form = MeetingForm()
    
    context = {
        'form': form,
        'title': 'Schedule New Meeting'
    }
    return render(request, 'governance/meeting_form.html', context)

@login_required
def edit_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meeting updated successfully!')
            return redirect('governance:meetings')
    else:
        form = MeetingForm(instance=meeting)
    
    context = {
        'form': form,
        'meeting': meeting,
        'title': 'Edit Meeting'
    }
    return render(request, 'governance/meeting_form.html', context)

@login_required
def delete_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    if request.method == 'POST':
        meeting.delete()
        messages.success(request, 'Meeting deleted successfully!')
        return redirect('governance:meetings')
    
    context = {
        'meeting': meeting
    }
    return render(request, 'governance/confirm_delete_meeting.html', context)

@login_required
def view_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    context = {
        'meeting': meeting
    }
    return render(request, 'governance/meeting_detail.html', context)

@login_required
def update_meeting_minutes(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    if request.method == 'POST':
        minutes = request.POST.get('minutes', '')
        meeting.minutes = minutes
        meeting.save()
        messages.success(request, 'Meeting minutes updated successfully!')
        return redirect('governance:view_meeting', meeting_id=meeting.id)
    
    context = {
        'meeting': meeting
    }
    return render(request, 'governance/meeting_minutes.html', context)

@login_required
def reports(request):
    reports_list = Report.objects.all()
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        reports_list = reports_list.filter(status=status_filter)
    
    # Filter by report type if provided
    type_filter = request.GET.get('type')
    if type_filter:
        reports_list = reports_list.filter(report_type=type_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        reports_list = reports_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'reports': reports_list,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search_query': search_query,
        'report_types': Report.REPORT_TYPE_CHOICES,
        'status_choices': Report.STATUS_CHOICES,
    }
    return render(request, 'governance/reports.html', context)


@login_required
def create_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            report.save()
            
            # Generate report data based on type
            _generate_report_data(report)
            
            messages.success(request, f'Report "{report.title}" has been generated successfully.')
            return redirect('governance:report_detail', pk=report.pk)
    else:
        form = ReportForm()
    
    return render(request, 'governance/report_form.html', {'form': form})


@login_required
def report_detail(request, pk):
    report = get_object_or_404(Report, pk=pk)
    return render(request, 'governance/report_detail.html', {'report': report})


@login_required
def delete_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        report_title = report.title
        report.delete()
        messages.success(request, f'Report "{report_title}" has been deleted successfully.')
        return redirect('governance:reports')
    return render(request, 'governance/confirm_delete_report.html', {'report': report})


def _generate_report_data(report):
    """Generate report data based on report type and period"""
    data = {}
    
    # Filter data by period
    policies = Policy.objects.filter(
        created_at__date__gte=report.period_start,
        created_at__date__lte=report.period_end
    )
    
    meetings = Meeting.objects.filter(
        date__date__gte=report.period_start,
        date__date__lte=report.period_end
    )
    
    if report.report_type == 'policy_compliance':
        data = {
            'total_policies': policies.count(),
            'active_policies': policies.filter(status='active').count(),
            'draft_policies': policies.filter(status='draft').count(),
            'policies_by_category': dict(policies.values('category').annotate(count=Count('id')).values_list('category', 'count')),
            'policies_due_for_review': Policy.objects.filter(
                review_date__lte=timezone.now().date() + timedelta(days=30)
            ).count(),
        }
    
    elif report.report_type == 'meeting_summary':
        data = {
            'total_meetings': meetings.count(),
            'completed_meetings': meetings.filter(status='completed').count(),
            'scheduled_meetings': meetings.filter(status='scheduled').count(),
            'cancelled_meetings': meetings.filter(status='cancelled').count(),
            'meetings_by_type': dict(meetings.values('meeting_type').annotate(count=Count('id')).values_list('meeting_type', 'count')),
        }
    
    elif report.report_type == 'governance_metrics':
        data = {
            'total_policies': Policy.objects.count(),
            'total_meetings': Meeting.objects.count(),
            'total_reports': Report.objects.count(),
            'active_policies': Policy.objects.filter(status='active').count(),
            'upcoming_meetings': Meeting.objects.filter(
                date__gte=timezone.now(),
                status='scheduled'
            ).count(),
            'policies_by_status': dict(Policy.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'meetings_by_status': dict(Meeting.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')),
        }
    
    elif report.report_type in ['quarterly_review', 'annual_summary']:
        data = {
            'period_policies': policies.count(),
            'period_meetings': meetings.count(),
            'policy_updates': policies.filter(version__gt='1.0').count(),
            'meeting_completion_rate': (
                meetings.filter(status='completed').count() / max(meetings.count(), 1)
            ) * 100,
            'policies_by_category': dict(policies.values('category').annotate(count=Count('id')).values_list('category', 'count')),
            'meetings_by_type': dict(meetings.values('meeting_type').annotate(count=Count('id')).values_list('meeting_type', 'count')),
        }
    
    # Update report with generated data
    report.data = data
    report.status = 'completed'
    report.save()
