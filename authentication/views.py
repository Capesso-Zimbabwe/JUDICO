from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

# Custom login view to handle authentication
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Record login time for time tracking
            record_user_login(request, user)
            return redirect('home')  # Redirect to home page after login
        else:
            return render(request, 'authentication/login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'authentication/login.html')

@login_required
def logout_view(request):
    # Record logout time for time tracking
    record_user_logout(request)
    logout(request)
    return redirect('login')

def record_user_login(request, user):
    """Record user login time for time tracking"""
    from hr_management.models import UserTimeSession, Employee
    from django.utils import timezone
    
    try:
        # Try to get employee record for the user
        employee = Employee.objects.get(user=user)
        
        # Check if there's an active session (user didn't logout properly)
        active_session = UserTimeSession.objects.filter(
            user=user,
            logout_time__isnull=True
        ).first()
        
        if active_session:
            # Update existing session with new login time
            active_session.login_time = timezone.now()
            active_session.save()
        else:
            # Create new session
            UserTimeSession.objects.create(
                user=user,
                employee=employee,
                login_time=timezone.now(),
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
    except Employee.DoesNotExist:
        # User is not an employee, skip time tracking
        pass
    except Exception as e:
        # Log error but don't break login process
        print(f"Error recording login time: {e}")

def record_user_logout(request):
    """Record user logout time for time tracking"""
    from hr_management.models import UserTimeSession
    from django.utils import timezone
    
    try:
        # Find active session for the user
        active_session = UserTimeSession.objects.filter(
            user=request.user,
            logout_time__isnull=True
        ).first()
        
        if active_session:
            active_session.logout_time = timezone.now()
            active_session.save()
            
            # Create time entry if session duration is significant
            create_time_entry_from_session(active_session)
    except Exception as e:
        # Log error but don't break logout process
        print(f"Error recording logout time: {e}")

def create_time_entry_from_session(session):
    """Create a time entry from a user session"""
    from hr_management.models import TimeEntry
    from django.utils import timezone
    
    try:
        if session.login_time and session.logout_time:
            # Calculate duration
            duration = session.logout_time - session.login_time
            hours_worked = round(duration.total_seconds() / 3600, 2)
            
            # Only create entry if session was longer than 15 minutes
            if hours_worked >= 0.25:  # 15 minutes
                TimeEntry.objects.create(
                    employee=session.employee,
                    date=session.login_time.date(),
                    start_time=session.login_time.time(),
                    end_time=session.logout_time.time(),
                    activity_type='administrative',
                    description=f'System login session - {session.login_time.strftime("%Y-%m-%d %H:%M")} to {session.logout_time.strftime("%H:%M")}',
                    hours_worked=hours_worked,
                    is_billable=False,
                    status='draft',
                    submitted_by=session.user,
                    notes=f'Automatically generated from login session. IP: {session.ip_address}'
                )
    except Exception as e:
        print(f"Error creating time entry from session: {e}")

# Password reset views will use Django's built-in views
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

class CustomPasswordResetView(PasswordResetView):
    template_name = 'authentication/password_reset.html'
    email_template_name = 'authentication/password_reset_email.html'
    subject_template_name = 'authentication/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'authentication/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'authentication/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'authentication/password_reset_complete.html'

# Time tracking API endpoints
@login_required
@require_http_methods(["POST"])
def start_time_tracking(request):
    """Start manual time tracking for a specific activity"""
    from hr_management.models import UserTimeSession, Employee
    from django.utils import timezone
    import json
    
    try:
        data = json.loads(request.body)
        activity_type = data.get('activity_type', 'administrative')
        description = data.get('description', 'Manual time tracking')
        client_case = data.get('client_case', '')
        
        # Check if user has an active session
        active_session = UserTimeSession.objects.filter(
            user=request.user,
            logout_time__isnull=True
        ).first()
        
        if active_session:
            return JsonResponse({'error': 'You already have an active time tracking session'}, status=400)
        
        # Get employee record
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'User is not an employee'}, status=400)
        
        # Create new manual time tracking session
        session = UserTimeSession.objects.create(
            user=request.user,
            employee=employee,
            login_time=timezone.now(),
            activity_type=activity_type,
            description=description,
            client_case=client_case,
            is_manual=True,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'start_time': session.login_time.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def stop_time_tracking(request):
    """Stop manual time tracking"""
    from hr_management.models import UserTimeSession
    from django.utils import timezone
    
    try:
        # Find active manual session
        active_session = UserTimeSession.objects.filter(
            user=request.user,
            logout_time__isnull=True,
            is_manual=True
        ).first()
        
        if not active_session:
            return JsonResponse({'error': 'No active time tracking session found'}, status=400)
        
        # Update session with logout time
        active_session.logout_time = timezone.now()
        active_session.save()
        
        # Create time entry
        create_time_entry_from_session(active_session)
        
        return JsonResponse({
            'success': True,
            'end_time': active_session.logout_time.isoformat(),
            'duration_hours': round((active_session.logout_time - active_session.login_time).total_seconds() / 3600, 2)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_time_tracking_status(request):
    """Get current time tracking status"""
    from hr_management.models import UserTimeSession
    from django.utils import timezone
    
    try:
        # Check for active session
        active_session = UserTimeSession.objects.filter(
            user=request.user,
            logout_time__isnull=True
        ).first()
        
        if active_session:
            duration = timezone.now() - active_session.login_time
            return JsonResponse({
                'is_tracking': True,
                'start_time': active_session.login_time.isoformat(),
                'duration_hours': round(duration.total_seconds() / 3600, 2),
                'activity_type': active_session.activity_type,
                'description': active_session.description,
                'is_manual': active_session.is_manual
            })
        else:
            return JsonResponse({'is_tracking': False})
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
