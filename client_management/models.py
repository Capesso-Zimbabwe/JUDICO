from django.db import models
from django.contrib.auth.models import User
from sequences import Sequence
from django.utils import timezone

# Add to existing models.py
from lawyer_portal.models import LawyerProfile

def generate_client_code():
    sequence_number = Sequence('clients').get_next_value()
    return f"CL{sequence_number:06d}"

def generate_case_code():
    sequence_number = Sequence('cases').get_next_value()
    return f"CS{sequence_number:06d}"

class Client(models.Model):
    CASE_TYPES = [
        ('civil', 'Civil Law'),
        ('criminal', 'Criminal Law'),
        ('corporate', 'Corporate Law'),
        ('family', 'Family Law'),
        ('employment', 'Employment Law'),
        ('real_estate', 'Real Estate Law'),
        ('intellectual_property', 'Intellectual Property'),
        ('tax', 'Tax Law'),
        ('immigration', 'Immigration Law'),
        ('personal_injury', 'Personal Injury'),
        ('contract', 'Contract Law'),
        ('bankruptcy', 'Bankruptcy Law'),
        ('other', 'Other'),
    ]
    code = models.CharField(max_length=200, default=generate_client_code, editable=False, unique=True)
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    case_type = models.CharField(max_length=50, choices=CASE_TYPES, default='other')
    registration_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    assigned_lawyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_clients')
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')
    
    def __str__(self):
        return self.name

class ClientDocument(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='client_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.client.name} - {self.title}"

class Case(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    code = models.CharField(max_length=200, default=generate_case_code, editable=False, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='cases')
    title = models.CharField(max_length=300)
    description = models.TextField()
    case_type = models.CharField(max_length=50, choices=Client.CASE_TYPES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_lawyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='cases')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    start_date = models.DateField(null=True, blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    court_date = models.DateTimeField(null=True, blank=True)
    court_location = models.CharField(max_length=200, blank=True)
    case_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    is_billable = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cases')
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    @property
    def progress_percentage(self):
        if self.status == 'completed' or self.status == 'closed':
            return 100
        elif self.status == 'cancelled':
            return 0
        else:
            updates_count = self.updates.count()
            if updates_count == 0:
                return 10 if self.status == 'active' else 5
            return min(90, 10 + (updates_count * 10))
    
    @property
    def days_since_creation(self):
        return (timezone.now().date() - self.created_date.date()).days
    
    @property
    def is_overdue(self):
        if self.expected_completion_date and self.status not in ['completed', 'closed', 'cancelled']:
            return timezone.now().date() > self.expected_completion_date
        return False

class CaseUpdate(models.Model):
    UPDATE_TYPES = [
        ('progress', 'Progress Update'),
        ('meeting', 'Meeting/Consultation'),
        ('document', 'Document Filed'),
        ('court', 'Court Appearance'),
        ('research', 'Legal Research'),
        ('communication', 'Client Communication'),
        ('milestone', 'Milestone Achieved'),
        ('issue', 'Issue/Problem'),
        ('resolution', 'Resolution'),
        ('other', 'Other'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=200)
    description = models.TextField()
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES, default='progress')
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_billable = models.BooleanField(default=True)
    next_action = models.TextField(blank=True)
    next_action_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.case.code} - {self.title}"

class CaseDocument(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='case_documents/')
    document_type = models.CharField(max_length=50, choices=[
        ('contract', 'Contract'),
        ('evidence', 'Evidence'),
        ('correspondence', 'Correspondence'),
        ('court_filing', 'Court Filing'),
        ('research', 'Legal Research'),
        ('other', 'Other'),
    ], default='other')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.case.code} - {self.title}"
