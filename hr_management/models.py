from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Employee(models.Model):
    # Add this field at the top of the model
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='employee_profile')
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='employees/profile_pictures/', null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    
    # Employment Information
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    max_days_allowed = models.PositiveIntegerField(default=0)
    requires_approval = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"
    
    @property
    def days_requested(self):
        delta = self.end_date - self.start_date
        return delta.days + 1

class PerformanceReview(models.Model):
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('in_progress', 'In Progress'),
        ('scheduled', 'Scheduled'),
        ('overdue', 'Overdue'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conducted_reviews')
    review_date = models.DateField()
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    overall_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    strengths = models.TextField(blank=True, null=True)
    areas_for_improvement = models.TextField(blank=True, null=True)
    goals = models.TextField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    employee_acknowledgment = models.BooleanField(default=False)
    acknowledgment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Review for {self.employee} - {self.review_date}"

class TimeEntry(models.Model):
    """Model for tracking employee time entries"""
    
    ACTIVITY_TYPES = [
        ('legal_research', 'Legal Research'),
        ('client_consultation', 'Client Consultation'),
        ('court_appearance', 'Court Appearance'),
        ('document_preparation', 'Document Preparation'),
        ('case_management', 'Case Management'),
        ('meeting', 'Meeting'),
        ('administrative', 'Administrative'),
        ('training', 'Training'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('billed', 'Billed'),
    ]
    
    # Employee and basic info
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Activity details
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField()
    client_case = models.CharField(max_length=200, blank=True, help_text="Client name or case reference")
    
    # Time tracking
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, help_text="Hours worked (e.g., 7.5)")
    
    # Billing and approval
    is_billable = models.BooleanField(default=True)
    billable_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    billable_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Approval chain
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_time_entries')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_time_entries')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional fields
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags for categorization")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name_plural = 'Time Entries'
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.hours_worked}h) - {self.get_activity_type_display()}"
    
    def save(self, *args, **kwargs):
        # Calculate hours worked if start and end time are provided
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            start_dt = datetime.combine(self.date, self.start_time)
            end_dt = datetime.combine(self.date, self.end_time)
            
            # Handle overnight entries
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            time_diff = end_dt - start_dt
            self.hours_worked = round(time_diff.total_seconds() / 3600, 2)
        
        # Calculate billable amount if rate and hours are provided
        if self.billable_rate and self.hours_worked and self.is_billable:
            self.billable_amount = self.billable_rate * self.hours_worked
        
        super().save(*args, **kwargs)
    
    @property
    def duration_formatted(self):
        """Return formatted duration string"""
        hours = int(self.hours_worked)
        minutes = int((self.hours_worked - hours) * 60)
        return f"{hours}h {minutes}m"
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_billed(self):
        return self.status == 'billed'


class UserTimeSession(models.Model):
    """Model for tracking user login/logout sessions for automatic time tracking"""
    
    ACTIVITY_TYPES = [
        ('legal_research', 'Legal Research'),
        ('client_consultation', 'Client Consultation'),
        ('court_appearance', 'Court Appearance'),
        ('document_preparation', 'Document Preparation'),
        ('case_management', 'Case Management'),
        ('meeting', 'Meeting'),
        ('administrative', 'Administrative'),
        ('training', 'Training'),
        ('other', 'Other'),
    ]
    
    # User and employee info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_sessions')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='time_sessions', null=True, blank=True)
    
    # Session timing
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)
    
    # Activity details (for manual tracking)
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES, default='administrative')
    description = models.TextField(blank=True)
    client_case = models.CharField(max_length=200, blank=True, help_text="Client name or case reference")
    
    # Session metadata
    is_manual = models.BooleanField(default=False, help_text="True if manually started, False if automatic from login")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-login_time']
        verbose_name = 'User Time Session'
        verbose_name_plural = 'User Time Sessions'
    
    def __str__(self):
        status = "Active" if self.logout_time is None else "Completed"
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M')} ({status})"
    
    @property
    def duration(self):
        """Calculate session duration"""
        if self.logout_time:
            return self.logout_time - self.login_time
        else:
            from django.utils import timezone
            return timezone.now() - self.login_time
    
    @property
    def duration_hours(self):
        """Get duration in hours"""
        return round(self.duration.total_seconds() / 3600, 2)
    
    @property
    def is_active(self):
        """Check if session is currently active"""
        return self.logout_time is None
    
    @property
    def duration_formatted(self):
        """Return formatted duration string"""
        duration = self.duration
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"