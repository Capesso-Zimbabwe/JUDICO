from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

from .models import UserTimeSession, Employee, TimeEntry


@receiver(user_logged_in)
def start_time_session(sender, user, request, **kwargs):
    """Start a new UserTimeSession when a user logs in if none is active."""
    # Close any orphan active sessions (safety)
    UserTimeSession.objects.filter(user=user, logout_time__isnull=True).update(logout_time=timezone.now())

    employee = None
    try:
        employee = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        employee = None

    UserTimeSession.objects.create(
        user=user,
        employee=employee,
        login_time=timezone.now(),
        activity_type='administrative',
        description='Auto session started at login',
        is_manual=False,
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
    )


@receiver(user_logged_out)
def stop_time_session(sender, user, request, **kwargs):
    """Stop the active session on logout and create TimeEntry records for the duration."""
    if user is None:
        return

    session = (
        UserTimeSession.objects
        .filter(user=user, logout_time__isnull=True)
        .order_by('-login_time')
        .first()
    )
    if not session:
        return

    session.logout_time = timezone.now()
    session.save(update_fields=['logout_time'])

    employee = session.employee
    if employee is None:
        # Try to resolve in case it was added later
        try:
            employee = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return  # Cannot create TimeEntry without employee

    # Split the session across days if needed and create TimeEntry per day
    start_dt = session.login_time.astimezone(timezone.get_current_timezone())
    end_dt = session.logout_time.astimezone(timezone.get_current_timezone())

    current_start = start_dt
    while current_start.date() <= end_dt.date():
        day_end = (current_start.replace(hour=23, minute=59, second=59, microsecond=999999))
        segment_end = end_dt if end_dt.date() == current_start.date() else day_end

        # Create TimeEntry for this segment
        TimeEntry.objects.create(
            employee=employee,
            date=current_start.date(),
            start_time=current_start.time(),
            end_time=segment_end.time(),
            activity_type='administrative',
            description='Auto from login/logout session',
            client_case='',
            is_billable=False,
            submitted_by=user,
        )

        # Move to next day start
        current_start = (day_end + timezone.timedelta(microseconds=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )


