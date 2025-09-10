from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from django.contrib.auth.hashers import make_password
import secrets
import string

from .models import Employee, Department, LeaveRequest, PerformanceReview, LeaveType
from .models import TimeEntry, UserTimeSession
from .forms import EmployeeForm, LeaveRequestForm, PerformanceReviewForm, UserCreationForm
from lawyer_portal.models import LawyerProfile
from client_management.models import Client
from client_portal.models import ClientProfile
from hr_management.forms import TimeEntryForm

@login_required
def hr_dashboard(request):
    # Get counts for dashboard
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(is_active=True).count()
    on_leave_count = LeaveRequest.objects.filter(status='approved', 
                                               start_date__lte=timezone.now().date(),
                                               end_date__gte=timezone.now().date()).count()
    pending_reviews = PerformanceReview.objects.filter(employee_acknowledgment=False).count()
    department_count = Department.objects.count()
    
    # Get department distribution data
    departments = Department.objects.annotate(employee_count=Count('employees'))
    department_labels = [dept.name for dept in departments]
    department_data = [dept.employee_count for dept in departments]
    
    # Get leave status distribution
    leave_status_counts = LeaveRequest.objects.values('status').annotate(count=Count('id'))
    leave_status_labels = [status['status'].capitalize() for status in leave_status_counts]
    leave_status_data = [status['count'] for status in leave_status_counts]
    
    # Get employee growth data (last 6 months)

    today = timezone.now().date()
    months = []
    employee_growth_data = []
    
    for i in range(5, -1, -1):
        # Calculate the month (going backwards from current month)
        month_date = today.replace(day=1)
        for _ in range(i):
            month_date = (month_date.replace(day=1) - timezone.timedelta(days=1)).replace(day=1)
        
        # Get the month name
        month_name = month_date.strftime('%b')
        months.append(month_name)
        
        # Count employees created in that month
        next_month = month_date.replace(month=month_date.month+1 if month_date.month < 12 else 1,
                                      year=month_date.year if month_date.month < 12 else month_date.year+1)
        
        count = Employee.objects.filter(
            created_at__gte=month_date,
            created_at__lt=next_month
        ).count()
        
        employee_growth_data.append(count)
    
    # Get performance review status data
    # Get performance review status data
    # Using employee_acknowledgment and other existing fields to categorize reviews
    today = timezone.now().date()
    
    # Example: Completed reviews are those with employee acknowledgment
    review_completed = PerformanceReview.objects.filter(employee_acknowledgment=True).count()
    
    # Example: In progress reviews are those without employee acknowledgment but with a review date in the past
    review_in_progress = PerformanceReview.objects.filter(
        employee_acknowledgment=False,
        review_date__lt=today
    ).count()
    
    # Example: Scheduled reviews are those with a future review date
    review_scheduled = PerformanceReview.objects.filter(review_date__gt=today).count()
    
    # Example: Overdue reviews might be those that are past the review date but not acknowledged
    review_overdue = PerformanceReview.objects.filter(
        employee_acknowledgment=False,
        review_date__lt=today - timezone.timedelta(days=14)  # Assuming 14 days grace period
    ).count()
    
    review_status_labels = ['Completed', 'In Progress', 'Scheduled', 'Overdue']
    review_status_data = [review_completed, review_in_progress, review_scheduled, review_overdue]
    
    # Get recent employees (last 5)
    recent_employees = Employee.objects.order_by('-created_at')[:5]
    
    # Get recent leave requests (last 5)
    recent_leave_requests = LeaveRequest.objects.select_related('employee').order_by('-created_at')[:5]
    
    # Calculate HR metrics
    # Employee retention rate (simplified calculation)
    total_employees_last_year = Employee.objects.filter(
        created_at__lt=today - timezone.timedelta(days=365)
    ).count()
    current_active = Employee.objects.filter(is_active=True).count()
    employee_retention = round((current_active / max(total_employees_last_year, 1)) * 100, 1) if total_employees_last_year > 0 else 95
    
    # Average review score (simplified - using a default since we don't have score field)
    avg_review_score = 4.2  # Default value
    
    # Leave approval rate
    total_leave_requests = LeaveRequest.objects.count()
    approved_leave_requests = LeaveRequest.objects.filter(status='approved').count()
    leave_approval_rate = round((approved_leave_requests / max(total_leave_requests, 1)) * 100, 1) if total_leave_requests > 0 else 88
    
    # Monthly hires (current month)
    current_month_start = today.replace(day=1)
    monthly_hires = Employee.objects.filter(created_at__gte=current_month_start).count()
    
    # HR status message
    hr_status = "All HR processes up to date"
    
    # Prepare context
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'on_leave_count': on_leave_count,
        'pending_reviews': pending_reviews,
        'department_count': department_count,
        'department_labels': department_labels,
        'department_data': department_data,
        'leave_status_labels': leave_status_labels,
        'leave_status_data': leave_status_data,
        'months': months,
        'employee_growth_data': employee_growth_data,
        'review_status_labels': review_status_labels,
        'review_status_data': review_status_data,
        'recent_employees': recent_employees,
        'recent_leave_requests': recent_leave_requests,
        'employee_retention': employee_retention,
        'avg_review_score': avg_review_score,
        'leave_approval_rate': leave_approval_rate,
        'monthly_hires': monthly_hires,
        'hr_status': hr_status,
    }
    
    return render(request, 'hr_management/dashboard.html', context)

@login_required
def employee_list(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    employees = Employee.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(position__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(is_active=True).count()
    inactive_employees = total_employees - active_employees
    
    # Pagination
    paginator = Paginator(employees, 10)  # Show 10 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'employees': page_obj,
        'page_obj': page_obj,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'search_query': search_query,
    }
    
    return render(request, 'hr_management/employee_list.html', context)

@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            
            # Get or create a User for this employee if not provided
            if not employee.user:
                # Create a username from email or name
                username = employee.email.split('@')[0]
                # Create a random password (or set a default one)
                password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                
                # Create the user
                user = User.objects.create_user(
                    username=username,
                    email=employee.email,
                    password=password,
                    first_name=employee.first_name,
                    last_name=employee.last_name
                )
                employee.user = user
            
            employee.save()
            
            # Check if employee should be registered as a lawyer
            user_type = form.cleaned_data.get('user_type')
            if user_type == 'lawyer':
                # Create lawyer profile if it doesn't exist
                if not hasattr(employee.user, 'lawyer_profile'):
                    LawyerProfile.objects.create(
                        user=employee.user,
                        specialization="General",  # Default value
                        years_of_experience=0,    # Default value
                    )
            
            messages.success(request, f'Employee {employee.full_name} created successfully!')
            if request.headers.get('HX-Request'):
                # Return success response for HTMX
                from django.http import HttpResponse
                return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
            return redirect('hr_management:employee_list')
        else:
            # Print form errors to console for debugging
            print(form.errors)
    else:
        form = EmployeeForm()
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'hr_management/employee_form_modal.html', {'form': form})
    
    departments = Department.objects.all()
    return render(request, 'hr_management/employee_form.html', {'form': form, 'departments': departments})

@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employee {employee.full_name} updated successfully!')
            if request.headers.get('HX-Request'):
                # Return success response for HTMX
                from django.http import HttpResponse
                return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
            return redirect('hr_management:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'hr_management/employee_form_modal.html', {'form': form, 'employee': employee})
    
    departments = Department.objects.all()
    return render(request, 'hr_management/employee_form.html', {'form': form, 'employee': employee, 'departments': departments})

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee.delete()
        messages.success(request, f'Employee {employee.full_name} deleted successfully!')
        return redirect('hr_management:employee_list')
    
    return render(request, 'hr_management/employee_confirm_delete.html', {'employee': employee})

@login_required
def leave_management(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    leave_requests = LeaveRequest.objects.all().order_by('-created_at')
    leave_types = LeaveType.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        leave_requests = leave_requests.filter(
            Q(employee__first_name__icontains=search_query) |
            Q(employee__last_name__icontains=search_query) |
            Q(leave_type__name__icontains=search_query) |
            Q(status__icontains=search_query) |
            Q(reason__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(leave_requests, 10)  # Show 10 leave requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get counts for different statuses
    pending_count = leave_requests.filter(status='pending').count()
    approved_count = leave_requests.filter(status='approved').count()
    rejected_count = leave_requests.filter(status='rejected').count()
    
    context = {
        'page_obj': page_obj,
        'leave_requests': page_obj,  # For backward compatibility
        'leave_types': leave_types,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'search_query': search_query,
    }
    
    return render(request, 'hr_management/leave_management.html', context)

@login_required
def leave_create_modal(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.request_date = timezone.now().date()
            leave_request.save()
            messages.success(request, f'Leave request for {leave_request.employee.full_name} created successfully!')
            if request.headers.get('HX-Request'):
                # Return success response for HTMX
                from django.http import HttpResponse
                return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
            return redirect('hr_management:leave_management')
        else:
            # Print form errors to console for debugging
            print(form.errors)
    else:
        form = LeaveRequestForm()
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'hr_management/leave_form_modal.html', {'form': form})
    
    return render(request, 'hr_management/leave_form.html', {'form': form})

@login_required
def performance_reviews(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    reviews = PerformanceReview.objects.all().order_by('-review_date')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        reviews = reviews.filter(
            Q(employee__first_name__icontains=search_query) |
            Q(employee__last_name__icontains=search_query) |
            Q(reviewer__first_name__icontains=search_query) |
            Q(reviewer__last_name__icontains=search_query) |
            Q(overall_rating__icontains=search_query)
        )
    
    # Get counts for different ratings (from all reviews, not just filtered)
    all_reviews = PerformanceReview.objects.all()
    excellent_count = all_reviews.filter(overall_rating=5).count()
    good_count = all_reviews.filter(overall_rating=4).count()
    average_count = all_reviews.filter(overall_rating=3).count()
    below_average_count = all_reviews.filter(overall_rating=2).count()
    poor_count = all_reviews.filter(overall_rating=1).count()
    
    # Pagination
    paginator = Paginator(reviews, 10)  # Show 10 reviews per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reviews': page_obj,
        'page_obj': page_obj,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'average_count': average_count,
        'below_average_count': below_average_count,
        'poor_count': poor_count,
        'search_query': search_query,
    }
    
    return render(request, 'hr_management/performance_reviews.html', context)

@login_required
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
    
    # Get list of lawyer user IDs
    lawyer_users = [lawyer.user.id for lawyer in LawyerProfile.objects.all()]
    
    # Get list of client user IDs
    client_users = [profile.user.id for profile in ClientProfile.objects.all()]
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,  # For backward compatibility
        'lawyer_users': lawyer_users,
        'client_users': client_users,
        'search_query': search_query,
    }
    
    return render(request, 'hr_management/manage_users.html', context)

@login_required
def manage_lawyers(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    users = User.objects.filter(is_staff=False, is_superuser=False).order_by('-date_joined')
    
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
    
    lawyers = LawyerProfile.objects.all()
    lawyer_users = [lawyer.user.id for lawyer in lawyers]
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,  # For backward compatibility
        'lawyer_users': lawyer_users,
        'search_query': search_query,
    }
    
    return render(request, 'hr_management/manage_lawyers.html', context)

@login_required
def toggle_lawyer(request, user_id):
    user = User.objects.get(id=user_id)
    
    # Check if user is already a lawyer
    if hasattr(user, 'lawyer_profile'):
        # Remove lawyer profile
        user.lawyer_profile.delete()
        messages.success(request, f"{user.get_full_name()} is no longer a lawyer.")
    else:
        # Create lawyer profile
        LawyerProfile.objects.create(
            user=user,
            specialization="General",  # Default value
            years_of_experience=0,    # Default value
        )
        messages.success(request, f"{user.get_full_name()} is now a lawyer.")
    
    # Redirect back to manage lawyers page
    return redirect('hr_management:manage_lawyers')

@login_required
def toggle_client(request, user_id):
    user = User.objects.get(id=user_id)
    
    # Check if user is already a client
    if hasattr(user, 'client_profile'):
        # Remove client profile and associated client record
        client_profile = user.client_profile
        client = client_profile.client
        client_profile.delete()
        client.delete()
        messages.success(request, f"{user.get_full_name()} is no longer a client.")
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
        
        messages.success(request, f"{user.get_full_name()} is now a client with an initial case created.")
    
    return redirect('hr_management:manage_users')

@login_required
def time_sheets(request):
    """View for managing employee time sheets and time tracking"""
    from django.core.paginator import Paginator
    from django.db.models import Q, Sum, Count
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Permissions and filters
    is_hr = request.user.is_staff or request.user.is_superuser
    selected_user_id = request.GET.get('user') if is_hr else None

    # Get time entries for the selected/current user if they're an employee
    time_entries = TimeEntry.objects.none()
    user_sessions = UserTimeSession.objects.none()
    current_session = None
    
    # Determine target user for detail view
    target_user = request.user
    if is_hr and selected_user_id:
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        try:
            target_user = UserModel.objects.get(id=selected_user_id)
        except UserModel.DoesNotExist:
            target_user = request.user

    # Ensure the target user has an Employee record; auto-create minimal if missing for self only
    employee = None
    try:
        employee = Employee.objects.get(user=target_user)
    except Employee.DoesNotExist:
        if target_user == request.user:
            auto_email = target_user.email or f"{target_user.username}+{target_user.id}@autogen.local"
            try:
                employee = Employee.objects.create(
                    user=target_user,
                    first_name=target_user.first_name or target_user.username or 'User',
                    last_name=target_user.last_name or 'User',
                    email=auto_email,
                    phone='-',
                    position='Staff',
                    hire_date=timezone.now().date(),
                )
            except Exception:
                employee = None
    
    if employee:
        # Get time entries
        time_entries = TimeEntry.objects.filter(employee=employee).order_by('-date', '-start_time')
        
        # Get user sessions
        user_sessions = UserTimeSession.objects.filter(user=target_user).order_by('-login_time')
        
        # Get current active session
        current_session = UserTimeSession.objects.filter(
            user=target_user,
            logout_time__isnull=True
        ).first()
    
    # Calculate statistics
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # Today's hours
    today_hours = time_entries.filter(date=today).aggregate(
        total=Sum('hours_worked')
    )['total'] or 0
    
    # This week's hours
    week_hours = time_entries.filter(
        date__gte=week_start,
        date__lte=today
    ).aggregate(
        total=Sum('hours_worked')
    )['total'] or 0
    
    # This month's hours
    month_hours = time_entries.filter(
        date__gte=month_start,
        date__lte=today
    ).aggregate(
        total=Sum('hours_worked')
    )['total'] or 0
    
    # Activity breakdown
    activity_breakdown = time_entries.filter(
        date__gte=month_start
    ).values('activity_type').annotate(
        total_hours=Sum('hours_worked'),
        count=Count('id')
    ).order_by('-total_hours')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        time_entries = time_entries.filter(
            Q(description__icontains=search_query) |
            Q(client_case__icontains=search_query) |
            Q(activity_type__icontains=search_query)
        )
    
    # Pagination for time entries
    paginator = Paginator(time_entries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # If there is an active session, include its running duration in the stats
    if current_session:
        from decimal import Decimal
        running_hours = Decimal(str(current_session.duration_hours))
        today_hours = (today_hours if today_hours else Decimal('0')) + running_hours
        week_hours = (week_hours if week_hours else Decimal('0')) + running_hours
        month_hours = (month_hours if month_hours else Decimal('0')) + running_hours

    # HR overview: team summaries
    team_overview = []
    if is_hr:
        from decimal import Decimal
        employees_qs = Employee.objects.select_related('user')

        # Pre-aggregate time entries for month, week, today
        month_aggs = TimeEntry.objects.filter(
            date__gte=month_start,
            date__lte=today
        ).values('employee').annotate(total=Sum('hours_worked'))
        week_aggs = TimeEntry.objects.filter(
            date__gte=week_start,
            date__lte=today
        ).values('employee').annotate(total=Sum('hours_worked'))
        today_aggs = TimeEntry.objects.filter(
            date=today
        ).values('employee').annotate(total=Sum('hours_worked'))

        month_map = {a['employee']: a['total'] for a in month_aggs}
        week_map = {a['employee']: a['total'] for a in week_aggs}
        today_map = {a['employee']: a['total'] for a in today_aggs}

        # Active sessions map
        active_sessions = UserTimeSession.objects.filter(logout_time__isnull=True)
        active_by_user = {s.user_id: s for s in active_sessions}

        search_q = request.GET.get('team_search')
        if search_q:
            employees_qs = employees_qs.filter(
                first_name__icontains=search_q
            ) | employees_qs.filter(last_name__icontains=search_q)

        for emp in employees_qs:
            t = Decimal(str(today_map.get(emp.id, 0) or 0))
            w = Decimal(str(week_map.get(emp.id, 0) or 0))
            m = Decimal(str(month_map.get(emp.id, 0) or 0))

            # Add running session if active
            sess = active_by_user.get(getattr(emp.user, 'id', None))
            running = Decimal('0')
            if sess:
                running = Decimal(str(sess.duration_hours))
                t += running
                w += running
                m += running

            team_overview.append({
                'employee': emp,
                'user': emp.user,
                'today_hours': round(t, 2),
                'week_hours': round(w, 2),
                'month_hours': round(m, 2),
                'active_session': sess,
            })

        # Sort by today's hours desc
        team_overview.sort(key=lambda x: x['today_hours'], reverse=True)

    context = {
        'page_title': 'Time Tracking & Timesheets',
        'page_obj': page_obj,
        'time_entries': page_obj,
        'user_sessions': user_sessions[:10],  # Show last 10 sessions
        'current_session': current_session,
        'today_hours': round(today_hours, 2),
        'week_hours': round(week_hours, 2),
        'month_hours': round(month_hours, 2),
        'activity_breakdown': activity_breakdown,
        'is_employee': hasattr(request.user, 'employee_profile'),
        'search_query': search_query,
        'is_hr': is_hr,
        'team_overview': team_overview,
        'selected_user_id': str(getattr(target_user, 'id', '')),
    }
    
    return render(request, 'hr_management/time_sheets.html', context)

@login_required
def create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_type = form.cleaned_data.get('user_type')
            
            # Create appropriate profile based on user type
            if user_type == 'lawyer':
                # Create lawyer profile
                LawyerProfile.objects.create(
                    user=user,
                    specialization="General",  # Default value
                    years_of_experience=0,    # Default value
                )
                messages.success(request, f'Lawyer {user.username} created successfully!')
            elif user_type == 'client':
                # Create client record
                client = Client.objects.create(
                    name=f"{user.first_name} {user.last_name}",
                    contact_person=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    phone="",  # Default empty, can be updated later
                    address="",  # Default empty, can be updated later
                    assigned_lawyer=None  # Can be assigned later
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
                messages.success(request, f'Client {user.username} created successfully!')
            else:
                messages.success(request, f'User {user.username} created successfully!')
            
            return redirect('hr_management:manage_users')
    else:
        form = UserCreationForm()
    
    return render(request, 'hr_management/create_user.html', {'form': form})

@login_required
def create_user_modal(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_type = form.cleaned_data.get('user_type')
            
            # Create appropriate profile based on user type
            if user_type == 'lawyer':
                # Create lawyer profile
                LawyerProfile.objects.create(
                    user=user,
                    specialization="General",  # Default value
                    years_of_experience=0,    # Default value
                )
                messages.success(request, f'Lawyer {user.username} created successfully!')
            elif user_type == 'client':
                # Create client record
                client = Client.objects.create(
                    name=f"{user.first_name} {user.last_name}",
                    contact_person=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    phone="",  # Default empty, can be updated later
                    address="",  # Default empty, can be updated later
                    assigned_lawyer=None  # Can be assigned later
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
                messages.success(request, f'Client {user.username} created successfully!')
            else:
                messages.success(request, f'User {user.username} created successfully!')
            
            # Return success response for HTMX
            from django.http import HttpResponse
            return HttpResponse(
                '<script>'
                'document.querySelector("[data-modal-hide=\'user-new-modal\']").click(); '
                'window.location.reload();'
                '</script>'
            )
    else:
        form = UserCreationForm()
    
    return render(request, 'hr_management/user_form_modal.html', {'form': form})

@login_required
def create_review_modal(request):
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save()
            messages.success(request, f'Performance review for {review.employee} created successfully!')
            
            # Return success response for HTMX
            from django.http import HttpResponse
            return HttpResponse(
                '<script>'
                'document.querySelector("[data-modal-hide=\'review-new-modal\']").click(); '
                'window.location.reload();'
                '</script>'
            )
    else:
        form = PerformanceReviewForm()
    
    return render(request, 'hr_management/review_form_modal.html', {'form': form})

@login_required
def create_time_entry_modal(request):
    if request.method == 'POST':
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            time_entry = form.save(commit=False)
            time_entry.submitted_by = request.user
            time_entry.save()
            messages.success(request, f'Time entry for {time_entry.employee} created successfully!')
            
            # Return success response for HTMX
            from django.http import HttpResponse
            return HttpResponse(
                '<script>'
                'document.querySelector("[data-modal-hide=\'time-entry-new-modal\']").click(); '
                'window.location.reload();'
                '</script>'
            )
    else:
        form = TimeEntryForm()
    
    return render(request, 'hr_management/time_entry_form_modal.html', {'form': form})

@login_required
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    
    # Don't allow deleting yourself or superusers
    if user != request.user and not user.is_superuser:
        user.delete()
        messages.success(request, f'User deleted successfully!')
    
    return redirect('hr_management:manage_users')
