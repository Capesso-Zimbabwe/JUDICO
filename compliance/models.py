from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Requirement(models.Model):
    CATEGORY_CHOICES = [
        ('regulatory', 'Regulatory'),
        ('internal', 'Internal Policies'),
        ('industry', 'Industry Standards'),
        ('legal', 'Legal Requirements'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Compliant', 'Compliant'),
        ('Non-Compliant', 'Non-Compliant'),
    ]
    
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_requirements')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"REQ-{self.id:04d}: {self.title}"


class Audit(models.Model):
    TYPE_CHOICES = [
        ('internal', 'Internal Audit'),
        ('external', 'External Audit'),
        ('compliance', 'Compliance Audit'),
        ('financial', 'Financial Audit'),
        ('operational', 'Operational Audit'),
    ]
    
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=255)
    audit_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    scheduled_date = models.DateField()
    completion_date = models.DateField(blank=True, null=True)
    auditor = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    findings = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_audits')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AUD-{self.id:04d}: {self.title}"
