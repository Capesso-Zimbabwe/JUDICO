from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Entity(models.Model):
    """Model for entities (individuals or organizations) to be screened"""
    ENTITY_TYPES = [
        ('individual', 'Individual'),
        ('organization', 'Organization'),
        ('vessel', 'Vessel'),
        ('aircraft', 'Aircraft'),
    ]
    
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    date_of_birth = models.DateField(null=True, blank=True)  # For individuals
    place_of_birth = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    identification_number = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"
    
    class Meta:
        verbose_name_plural = "Entities"

class WatchList(models.Model):
    """Model for different watch lists (sanctions, PEP, etc.)"""
    LIST_TYPES = [
        ('sanctions', 'Sanctions List'),
        ('pep', 'Politically Exposed Persons'),
        ('terrorism', 'Terrorism Watch List'),
        ('crime', 'Criminal Watch List'),
        ('custom', 'Custom List'),
    ]
    
    name = models.CharField(max_length=255)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES)
    source = models.CharField(max_length=255)  # e.g., OFAC, UN, EU
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.source})"

class WatchListEntry(models.Model):
    """Individual entries in watch lists"""
    watch_list = models.ForeignKey(WatchList, on_delete=models.CASCADE, related_name='entries')
    name = models.CharField(max_length=255)
    aliases = models.TextField(null=True, blank=True)  # JSON field for alternative names
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    identification_numbers = models.TextField(null=True, blank=True)  # JSON field
    addresses = models.TextField(null=True, blank=True)  # JSON field
    reason_for_listing = models.TextField(null=True, blank=True)
    date_listed = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.watch_list.name}"

class Screening(models.Model):
    """Model for screening requests"""
    SCREENING_TYPES = [
        ('customer_onboarding', 'Customer Onboarding'),
        ('transaction_monitoring', 'Transaction Monitoring'),
        ('periodic_review', 'Periodic Review'),
        ('ad_hoc', 'Ad-hoc Screening'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('flagged', 'Flagged'),
        ('cleared', 'Cleared'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='screenings')
    screening_type = models.CharField(max_length=30, choices=SCREENING_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, null=True, blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_screenings')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_screenings')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Screening #{self.id} - {self.entity.name}"
    
    @property
    def subject(self):
        return self.entity.name
    
    @property
    def type(self):
        return self.get_screening_type_display()
    
    @property
    def date(self):
        return self.created_at.strftime('%Y-%m-%d')

class ScreeningResult(models.Model):
    """Model for individual screening results/matches"""
    MATCH_TYPES = [
        ('exact', 'Exact Match'),
        ('partial', 'Partial Match'),
        ('phonetic', 'Phonetic Match'),
        ('fuzzy', 'Fuzzy Match'),
    ]
    
    screening = models.ForeignKey(Screening, on_delete=models.CASCADE, related_name='results')
    watch_list_entry = models.ForeignKey(WatchListEntry, on_delete=models.CASCADE)
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES)
    match_score = models.FloatField()  # 0.0 to 1.0
    is_false_positive = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Match: {self.screening.entity.name} -> {self.watch_list_entry.name}"

class Transaction(models.Model):
    """Model for financial transactions to be monitored"""
    TRANSACTION_TYPES = [
        ('wire_transfer', 'Wire Transfer'),
        ('cash_deposit', 'Cash Deposit'),
        ('cash_withdrawal', 'Cash Withdrawal'),
        ('check_deposit', 'Check Deposit'),
        ('ach_transfer', 'ACH Transfer'),
        ('international_transfer', 'International Transfer'),
    ]
    
    transaction_id = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    sender_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='received_transactions')
    transaction_date = models.DateTimeField()
    description = models.TextField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency}"

class Alert(models.Model):
    """Model for AML alerts generated by the system"""
    ALERT_TYPES = [
        ('screening_match', 'Screening Match'),
        ('suspicious_transaction', 'Suspicious Transaction'),
        ('threshold_breach', 'Threshold Breach'),
        ('pattern_detection', 'Pattern Detection'),
        ('manual_review', 'Manual Review Required'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('closed', 'Closed'),
    ]
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    screening = models.ForeignKey(Screening, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Alert #{self.id} - {self.title}"
