from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone

from .models import Employee, Department, LeaveRequest, PerformanceReview, LeaveType
from .forms import EmployeeForm, LeaveRequestForm, PerformanceReviewForm, UserCreationForm
from lawyer_portal.models import LawyerProfile
from client_management.models import Client
from client_portal.models import ClientProfile

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
    }
    
    return render(request, 'hr_management/dashboard.html', context)

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    total_employees = employees.count()
    active_employees = employees.filter(is_active=True).count()
    inactive_employees = total_employees - active_employees
    
    context = {
        'employees': employees,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
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
                password = User.objects.make_random_password()
                
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
            return redirect('hr_management:employee_list')
        else:
            # Print form errors to console for debugging
            print(form.errors)
    else:
        form = EmployeeForm()
    
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
            return redirect('hr_management:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    
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
    leave_requests = LeaveRequest.objects.all().order_by('-created_at')
    leave_types = LeaveType.objects.all()
    
    # Get counts for different statuses
    pending_count = leave_requests.filter(status='pending').count()
    approved_count = leave_requests.filter(status='approved').count()
    rejected_count = leave_requests.filter(status='rejected').count()
    
    context = {
        'leave_requests': leave_requests,
        'leave_types': leave_types,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'hr_management/leave_management.html', context)

@login_required
def performance_reviews(request):
    reviews = PerformanceReview.objects.all().order_by('-review_date')
    
    # Get counts for different ratings
    excellent_count = reviews.filter(overall_rating=5).count()
    good_count = reviews.filter(overall_rating=4).count()
    average_count = reviews.filter(overall_rating=3).count()
    below_average_count = reviews.filter(overall_rating=2).count()
    poor_count = reviews.filter(overall_rating=1).count()
    
    context = {
        'reviews': reviews,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'average_count': average_count,
        'below_average_count': below_average_count,
        'poor_count': poor_count,
    }
    
    return render(request, 'hr_management/performance_reviews.html', context)

@login_required
def manage_users(request):
    users = User.objects.filter(is_superuser=False)
    
    # Get list of lawyer user IDs
    lawyer_users = [lawyer.user.id for lawyer in LawyerProfile.objects.all()]
    
    # Get list of client user IDs
    client_users = [profile.user.id for profile in ClientProfile.objects.all()]
    
    context = {
        'users': users,
        'lawyer_users': lawyer_users,
        'client_users': client_users,
    }
    
    return render(request, 'hr_management/manage_users.html', context)

@login_required
def manage_lawyers(request):
    users = User.objects.filter(is_staff=False, is_superuser=False)
    lawyers = LawyerProfile.objects.all()
    lawyer_users = [lawyer.user.id for lawyer in lawyers]
    
    context = {
        'users': users,
        'lawyer_users': lawyer_users,
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
def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    
    # Don't allow deleting yourself or superusers
    if user != request.user and not user.is_superuser:
        user.delete()
        messages.success(request, f'User deleted successfully!')
    
    return redirect('hr_management:manage_users')
