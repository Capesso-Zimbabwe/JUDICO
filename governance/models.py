from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Policy(models.Model):
    CATEGORY_CHOICES = [
        ('security', 'Security'),
        ('compliance', 'Compliance'),
        ('hr', 'Human Resources'),
        ('finance', 'Finance'),
        ('operations', 'Operations'),
        ('legal', 'Legal'),
        ('it', 'Information Technology'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    version = models.CharField(max_length=10, default='1.0')
    effective_date = models.DateField()
    review_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    document_file = models.FileField(upload_to='policies/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_policies')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_policies')
    
    class Meta:
        verbose_name_plural = 'Policies'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title


class Meeting(models.Model):
    MEETING_TYPE_CHOICES = [
        ('board', 'Board Meeting'),
        ('committee', 'Committee Meeting'),
        ('general', 'General Meeting'),
        ('emergency', 'Emergency Meeting'),
        ('quarterly', 'Quarterly Review'),
        ('annual', 'Annual Meeting'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    date = models.DateTimeField()
    duration = models.DurationField(help_text="Meeting duration (e.g., 1:30:00 for 1 hour 30 minutes)")
    location = models.CharField(max_length=200, blank=True, help_text="Physical location or meeting room")
    virtual_link = models.URLField(blank=True, help_text="Video conference link")
    agenda = models.TextField(blank=True)
    minutes = models.TextField(blank=True, help_text="Meeting minutes/notes")
    attendees = models.ManyToManyField(User, related_name='meetings_attended', blank=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_meetings')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Meetings'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.date.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_upcoming(self):
        return self.date > timezone.now() and self.status == 'scheduled'
    
    @property
    def is_today(self):
        return self.date.date() == timezone.now().date()


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('policy_compliance', 'Policy Compliance Report'),
        ('meeting_summary', 'Meeting Summary Report'),
        ('governance_metrics', 'Governance Metrics Report'),
        ('quarterly_review', 'Quarterly Review Report'),
        ('annual_summary', 'Annual Summary Report'),
        ('custom', 'Custom Report'),
    ]
    
    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    period_start = models.DateField(help_text="Report period start date")
    period_end = models.DateField(help_text="Report period end date")
    data = models.JSONField(default=dict, help_text="Report data and metrics")
    file_path = models.FileField(upload_to='reports/', blank=True, null=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.period_start} - {self.period_end})"
    
    @property
    def period_display(self):
        return f"{self.period_start.strftime('%b %Y')} - {self.period_end.strftime('%b %Y')}"
