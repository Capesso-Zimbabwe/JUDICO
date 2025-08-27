from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, FileResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from client_management.models import Client
from client_portal.models import ClientProfile
# Import other models as needed
from lawyer_portal.views import is_lawyer  # Import the is_lawyer function
from client_portal.views import is_client  # Import the is_client function
from governance.models import Report
import os
import json
from datetime import datetime, timedelta

def is_staff(user):
    return user.is_staff

# Add this new home view
def home(request):
    # If user is authenticated and staff, redirect to admin dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_portal:admin_dashboard')
    # If user is authenticated and is a lawyer, redirect to lawyer dashboard
    elif request.user.is_authenticated and is_lawyer(request.user):
        return redirect('lawyer_portal:dashboard')
    # If user is authenticated and is a client, redirect to client portal
    elif request.user.is_authenticated and is_client(request.user):
        return redirect('client_portal:dashboard')
    # Otherwise show a welcome page
    return render(request, 'admin_portal/home.html', {})

@login_required
@user_passes_test(is_staff)
def admin_dashboard(request):
    # Get counts for various models
    from task_management.models import Task
    from document_repository.models import Document, DocumentCategory
    from governance.models import Policy, Meeting, Report
    from lawyer_portal.models import LawyerProfile
    from contract_management.models import Contract, ContractTemplate
    import json
    from django.db.models import Count, Q, Sum
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Basic counts
    client_count = Client.objects.count()
    lawyer_count = LawyerProfile.objects.count()
    task_count = Task.objects.count()
    document_count = Document.objects.count()
    
    # Task status counts
    task_pending_count = Task.objects.filter(status='pending').count()
    task_in_progress_count = Task.objects.filter(status='in_progress').count()
    task_completed_count = Task.objects.filter(status='completed').count()
    task_on_hold_count = Task.objects.filter(status='on_hold').count()
    
    # Contract counts
    contract_count = Contract.objects.count()
    active_contracts_count = Contract.objects.filter(status='active').count()
    pending_contracts_count = Contract.objects.filter(status='pending_signature').count()
    expired_contracts_count = Contract.objects.filter(status='expired').count()
    contract_templates_count = ContractTemplate.objects.count()
    

    
    # Document type counts
    client_document_count = Document.objects.filter(category__name__icontains='client').count()
    lawyer_document_count = Document.objects.filter(category__name__icontains='lawyer').count()
    case_document_count = Document.objects.filter(category__name__icontains='case').count()
    admin_document_count = Document.objects.filter(category__name__icontains='admin').count()
    
    # Client growth data (last 6 months)
    today = timezone.now().date()
    six_months_ago = today - timedelta(days=180)
    months = []
    client_growth_data = []
    
    for i in range(6):
        month_date = six_months_ago + timedelta(days=30 * i)
        month_name = month_date.strftime('%b')
        months.append(month_name)
        
        # Count clients registered in this month
        month_start = month_date.replace(day=1)
        if i < 5:
            next_month = month_date.replace(day=1) + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(days=1)
        else:
            month_end = today
            
        month_clients = Client.objects.filter(
            registration_date__gte=month_start,
            registration_date__lte=month_end
        ).count()
        client_growth_data.append(month_clients)
    
    # Lawyer specialization data
    lawyer_specializations = LawyerProfile.objects.values('specialization').annotate(
        count=Count('specialization')
    ).order_by('-count')[:5]  # Top 5 specializations
    
    lawyer_specialization_labels = [item['specialization'] for item in lawyer_specializations]
    lawyer_specialization_data = [item['count'] for item in lawyer_specializations]
    
    # Governance data
    active_policies_count = Policy.objects.filter(status='active').count()
    scheduled_meetings_count = Meeting.objects.filter(status='scheduled').count()
    pending_reviews_count = Policy.objects.filter(review_date__lte=today + timedelta(days=30)).count()
    compliance_reports_count = Report.objects.filter(report_type='policy_compliance').count()
    
    # Recent items
    recent_tasks = Task.objects.all().order_by('-created_at')[:5]
    recent_documents = Document.objects.all().order_by('-uploaded_at')[:5]
    recent_contracts = Contract.objects.all().order_by('-created_at')[:5]
    
    # Overdue and urgent items
    overdue_tasks = Task.objects.filter(
        Q(status__in=['pending', 'in_progress']) & 
        Q(due_date__lt=today)
    ).count()
    
    due_this_week = Task.objects.filter(
        Q(status__in=['pending', 'in_progress']) & 
        Q(due_date__gte=today) & 
        Q(due_date__lte=today + timedelta(days=7))
    ).count()
    

    
    context = {
        'client_count': client_count,
        'lawyer_count': lawyer_count,
        'task_count': task_count,
        'document_count': document_count,
        'contract_count': contract_count,
        
        # Task data
        'task_pending_count': task_pending_count,
        'task_in_progress_count': task_in_progress_count,
        'task_completed_count': task_completed_count,
        'task_on_hold_count': task_on_hold_count,
        'overdue_tasks': overdue_tasks,
        'due_this_week': due_this_week,
        
        # Contract data
        'active_contracts_count': active_contracts_count,
        'pending_contracts_count': pending_contracts_count,
        'expired_contracts_count': expired_contracts_count,
        'contract_templates_count': contract_templates_count,
        

        
        # Document data
        'client_document_count': client_document_count,
        'lawyer_document_count': lawyer_document_count,
        'case_document_count': case_document_count,
        'admin_document_count': admin_document_count,
        
        # Charts data
        'client_growth_labels': json.dumps(months),
        'client_growth_data': json.dumps(client_growth_data),

        'lawyer_specialization_labels': json.dumps(lawyer_specialization_labels),
        'lawyer_specialization_data': json.dumps(lawyer_specialization_data),
        
        # Recent items
        'recent_tasks': recent_tasks,
        'recent_documents': recent_documents,
        'recent_contracts': recent_contracts,
        
        # Governance data
        'active_policies_count': active_policies_count,
        'scheduled_meetings_count': scheduled_meetings_count,
        'pending_reviews_count': pending_reviews_count,
        'compliance_reports_count': compliance_reports_count,
    }
    
    return render(request, 'admin_portal/dashboard.html', context)

# Add to existing views.py
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms

# Add this custom form for admin user creation
class AdminUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # Add user type selection field
    USER_TYPES = (
        ('regular', 'Regular User'),
        ('lawyer', 'Lawyer'),
        ('client', 'Client'),
    )
    user_type = forms.ChoiceField(choices=USER_TYPES, required=True, label='User Type')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'user_type')

@login_required
@user_passes_test(is_staff)
def manage_lawyers(request):
    users = User.objects.filter(is_staff=False, is_superuser=False)
    lawyers = LawyerProfile.objects.all()
    lawyer_users = [lawyer.user.id for lawyer in lawyers]
    
    context = {
        'users': users,
        'lawyer_users': lawyer_users,
    }
    
    return render(request, 'admin_portal/manage_lawyers.html', context)

@login_required
@user_passes_test(is_staff)
def manage_users(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get list of client user IDs - users who have ClientProfile records
    client_users = [profile.user.id for profile in ClientProfile.objects.all()]
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,  # For backward compatibility
        'lawyer_users': [lawyer.user.id for lawyer in LawyerProfile.objects.all()],
        'client_users': client_users,
        'search_query': search_query,
    }
    
    return render(request, 'admin_portal/manage_users.html', context)

@login_required
@user_passes_test(is_staff)
def toggle_lawyer(request, user_id):
    user = User.objects.get(id=user_id)
    
    # Check if user is already a lawyer
    if hasattr(user, 'lawyer_profile'):
        # Remove lawyer profile
        user.lawyer_profile.delete()
        message = f"{user.get_full_name()} is no longer a lawyer."
    else:
        # Create lawyer profile
        LawyerProfile.objects.create(
            user=user,
            specialization="General",  # Default value
            years_of_experience=0,    # Default value
        )
        message = f"{user.get_full_name()} is now a lawyer."
    
    # Redirect back to the referring page or manage users by default
    referer = request.META.get('HTTP_REFERER', '')
    if 'manage_lawyers' in referer:
        return redirect('admin_portal:manage_lawyers')
    else:
        return redirect('admin_portal:manage_users')

@login_required
@user_passes_test(is_staff)
def toggle_client(request, user_id):
    user = User.objects.get(id=user_id)
    
    # Check if user is already a client
    if hasattr(user, 'client_profile'):
        # Remove client profile and associated client record
        client_profile = user.client_profile
        client = client_profile.client
        client_profile.delete()
        client.delete()
        message = f"{user.get_full_name()} is no longer a client."
    else:
        # Create client record and client profile
        client = Client.objects.create(
            name=f"{user.first_name} {user.last_name}",
            contact_person=user.get_full_name(),
            email=user.email,
            phone="",  # Default empty value
            address="",  # Default empty value
            assigned_lawyer=None  # No lawyer assigned initially
        )
        ClientProfile.objects.create(
            user=user,
            client=client
        )
        
        # Create a default case for the new client
        from client_management.models import Case
        Case.objects.create(
            client=client,
            title=f"Initial Consultation - {client.name}",
            description=f"Initial case consultation and legal assessment for {client.name}.",
            case_type=client.case_type,
            status='pending',
            priority='medium',
            created_by=request.user
        )
        
        message = f"{user.get_full_name()} is now a client with an initial case created."
    
    return redirect('admin_portal:manage_users')

@login_required
@user_passes_test(is_staff)
def create_user(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_type = form.cleaned_data.get('user_type')
            
            # Handle user type
            if user_type == 'lawyer':
                # Create lawyer profile
                LawyerProfile.objects.create(
                    user=user,
                    specialization="General",  # Default value
                    years_of_experience=0,    # Default value
                )
            elif user_type == 'client':
                # Create client entry
                client = Client.objects.create(
                    name=f"{user.first_name} {user.last_name}",
                    contact_person=user.get_full_name(),
                    email=user.email,
                    phone="",  # Default empty value
                    address="",  # Default empty value
                    assigned_lawyer=None  # No lawyer assigned initially
                )
                # Create client profile
                ClientProfile.objects.create(
                    user=user,
                    client=client
                )
                
                # Create a default case for the new client
                from client_management.models import Case
                Case.objects.create(
                    client=client,
                    title=f"Initial Consultation - {client.name}",
                    description=f"Initial case consultation and legal assessment for {client.name}.",
                    case_type=client.case_type,
                    status='pending',
                    priority='medium',
                    created_by=user
                )
            
            return redirect('admin_portal:manage_users')
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'admin_portal/create_user.html', {'form': form})
from lawyer_portal.models import LawyerProfile


@login_required
@user_passes_test(is_staff)
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    
    # Don't allow deleting yourself or superusers
    if user != request.user and not user.is_superuser:
        user.delete()
    
    return redirect('admin_portal:manage_users')


@login_required
@user_passes_test(is_staff)
def reports(request):
    # Get filter parameters from request
    module_filter = request.GET.get('module', '')
    report_type = request.GET.get('report_type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Import all report models from different modules
    from governance.models import Report as GovernanceReport
    from finance_management.models import Report as FinanceReport
    from transaction_support.models import TransactionReport
    from kyc_app.models import KYCReport
    
    # Collect all reports from different modules
    all_reports = []
    
    # Governance Reports
    governance_reports = GovernanceReport.objects.all()
    for report in governance_reports:
        all_reports.append({
            'id': report.id,
            'title': report.title,
            'module': 'Governance',
            'report_type': report.get_report_type_display(),
            'status': report.get_status_display(),
            'created_at': report.created_at,
            'generated_by': report.generated_by.username if report.generated_by else 'System',
            'period': report.period_display if hasattr(report, 'period_display') else '',
            'file_path': report.file_path,
            'description': report.description,
            'module_slug': 'governance',
            'status_value': report.status,
            'report_type_value': report.report_type
        })
    
    # Finance Reports
    finance_reports = FinanceReport.objects.all()
    for report in finance_reports:
        all_reports.append({
            'id': report.id,
            'title': report.name,
            'module': 'Finance',
            'report_type': report.get_report_type_display(),
            'status': report.get_status_display(),
            'created_at': report.created_at,
            'generated_by': report.generated_by.username if report.generated_by else 'System',
            'period': f"{report.start_date.strftime('%b %Y')} - {report.end_date.strftime('%b %Y')}" if report.start_date and report.end_date else '',
            'file_path': report.file_path,
            'description': report.description,
            'module_slug': 'finance',
            'status_value': report.status,
            'report_type_value': report.report_type
        })
    
    # Transaction Reports
    transaction_reports = TransactionReport.objects.all()
    for report in transaction_reports:
        all_reports.append({
            'id': report.id,
            'title': report.title,
            'module': 'Transaction Support',
            'report_type': report.get_report_type_display(),
            'status': 'Completed' if report.report_file else 'Pending',
            'created_at': report.generated_at,
            'generated_by': report.generated_by.username if report.generated_by else 'System',
            'period': '',
            'file_path': report.report_file.path if report.report_file else '',
            'description': report.description,
            'module_slug': 'transaction',
            'status_value': 'completed' if report.report_file else 'pending',
            'report_type_value': report.report_type
        })
    
    # KYC Reports
    kyc_reports = KYCReport.objects.all()
    for report in kyc_reports:
        all_reports.append({
            'id': report.id,
            'title': f"KYC Report #{report.report_id}",
            'module': 'KYC',
            'report_type': report.get_report_type_display(),
            'status': 'Completed' if report.pdf_report else 'Pending',
            'created_at': report.generated_at,
            'generated_by': report.generated_by,
            'period': '',
            'file_path': report.pdf_report.path if report.pdf_report else '',
            'description': report.summary,
            'module_slug': 'kyc',
            'status_value': 'completed' if report.pdf_report else 'pending',
            'report_type_value': report.report_type
        })
    
    # Apply filters
    if module_filter:
        all_reports = [r for r in all_reports if r['module'].lower() == module_filter.lower()]
    
    if report_type:
        all_reports = [r for r in all_reports if report_type.lower() in r['report_type_value'].lower()]
    
    if status:
        all_reports = [r for r in all_reports if status.lower() in r['status_value'].lower()]
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            all_reports = [r for r in all_reports if r['created_at'].date() >= date_from_obj]
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            all_reports = [r for r in all_reports if r['created_at'].date() <= date_to_obj]
        except ValueError:
            pass
    
    # Sort by creation date (most recent first)
    all_reports.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Paginate the results
    paginator = Paginator(all_reports, 10)  # Show 10 reports per page
    page_number = request.GET.get('page', 1)
    reports_page = paginator.get_page(page_number)
    
    # Get unique modules and report types for filters
    modules = list(set([r['module'] for r in all_reports]))
    report_types = list(set([r['report_type'] for r in all_reports]))
    statuses = list(set([r['status'] for r in all_reports]))
    
    context = {
        'reports': reports_page,
        'modules': modules,
        'report_types': report_types,
        'statuses': statuses,
        'current_filters': {
            'module': module_filter,
            'report_type': report_type,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'admin_portal/reports.html', context)


@login_required
@user_passes_test(is_staff)
def generate_report(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        report_type = request.POST.get('report_type')
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        description = request.POST.get('description', '')
        
        # Validate required fields
        if not all([title, report_type, period_start, period_end]):
            messages.error(request, 'Please fill in all required fields')
            return redirect('admin_portal:reports')
        
        try:
            # Convert string dates to datetime objects
            period_start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
            period_end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            # Create the report
            report = Report.objects.create(
                title=title,
                report_type=report_type,
                status='generating',  # Initial status
                period_start=period_start_date,
                period_end=period_end_date,
                description=description,
                generator=request.user.username,
                data=json.dumps({})  # Empty JSON data initially
            )
            
            # In a real application, you would start a background task to generate the report
            # For this example, we'll simulate a completed report after a short delay
            
            # Simulate report generation (in a real app, this would be a background task)
            # For demo purposes, we'll just update the status and create a dummy file path
            report.status = 'completed'
            report.file_path = f'reports/{report.id}_{report.title.replace(" ", "_")}.pdf'
            report.save()
            
            messages.success(request, f'Report "{title}" has been generated successfully')
        except Exception as e:
            messages.error(request, f'Error generating report: {str(e)}')
        
        return redirect('admin_portal:reports')
    
    # If not POST, redirect to reports page
    return redirect('admin_portal:reports')


@login_required
@user_passes_test(is_staff)
def view_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    # In a real application, you would render a template with the report details
    # For this example, we'll just redirect to the reports page with a message
    messages.info(request, f'Viewing report: {report.title}')
    
    # You could create a dedicated template for viewing reports
    # return render(request, 'admin_portal/view_report.html', {'report': report})
    
    # For now, just redirect back to reports
    return redirect('admin_portal:reports')


@login_required
@user_passes_test(is_staff)
def download_report(request, report_id):
    # Try to find the report in different models
    report = None
    report_type = None
    
    # Check governance reports
    try:
        from governance.models import Report as GovernanceReport
        report = GovernanceReport.objects.get(id=report_id)
        report_type = 'governance'
    except:
        pass
    
    # Check finance reports
    if not report:
        try:
            from finance_management.models import Report as FinanceReport
            report = FinanceReport.objects.get(id=report_id)
            report_type = 'finance'
        except:
            pass
    
    # Check transaction reports
    if not report:
        try:
            from transaction_support.models import TransactionReport
            report = TransactionReport.objects.get(id=report_id)
            report_type = 'transaction'
        except:
            pass
    
    # Check KYC reports
    if not report:
        try:
            from kyc_app.models import KYCReport
            report = KYCReport.objects.get(id=report_id)
            report_type = 'kyc'
        except:
            pass
    
    if not report:
        messages.error(request, 'Report not found')
        return redirect('admin_portal:reports')
    
    # Generate filename based on report type and title
    if report_type == 'governance':
        filename = f"{report.title.replace(' ', '_')}_{report.id}.pdf"
        title = report.title
        report_type_name = report.get_report_type_display()
        period = f"{report.period_start} to {report.period_end}" if hasattr(report, 'period_start') and hasattr(report, 'period_end') else 'N/A'
        generated_by = getattr(report, 'generator', 'System')
        created_at = report.created_at
    elif report_type == 'finance':
        filename = f"Finance_Report_{report.id}.pdf"
        title = report.name
        report_type_name = report.get_report_type_display()
        period = f"{report.start_date.strftime('%b %Y')} - {report.end_date.strftime('%b %Y')}" if hasattr(report, 'start_date') and hasattr(report, 'end_date') else 'N/A'
        generated_by = report.generated_by.username if report.generated_by else 'System'
        created_at = report.created_at
    elif report_type == 'transaction':
        filename = f"Transaction_Report_{report.id}.pdf"
        title = report.title
        report_type_name = report.get_report_type_display()
        period = 'N/A'
        generated_by = report.generated_by.username if report.generated_by else 'System'
        created_at = report.generated_at
    elif report_type == 'kyc':
        filename = f"KYC_Report_{report.report_id}.pdf"
        title = f"KYC Report #{report.report_id}"
        report_type_name = report.get_report_type_display()
        period = 'N/A'
        generated_by = report.generated_by if hasattr(report, 'generated_by') else 'System'
        created_at = report.generated_at
    
    # Create a response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Write report content to the response
    response.write(f"Report: {title}\n")
    response.write(f"Type: {report_type_name}\n")
    response.write(f"Period: {period}\n")
    response.write(f"Generated by: {generated_by}\n")
    response.write(f"Generated at: {created_at}\n")
    response.write(f"\nThis is a sample report content. In a real application, this would be a PDF document.")
    
    return response
