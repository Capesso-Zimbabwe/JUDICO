from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from client_management.models import Client, Case
from contract_management.models import Contract
from sequences import Sequence
import uuid

def generate_transaction_code():
    sequence_number = Sequence('transactions').get_next_value()
    return f"TXN{sequence_number:06d}"

class Transaction(models.Model):
    """Main transaction workspace for deals like M&A, financing, restructuring"""
    TRANSACTION_TYPES = [
        ('merger', 'Merger'),
        ('acquisition', 'Acquisition'),
        ('financing', 'Financing'),
        ('restructuring', 'Restructuring'),
        ('joint_venture', 'Joint Venture'),
        ('ipo', 'Initial Public Offering'),
        ('divestiture', 'Divestiture'),
        ('spin_off', 'Spin-off'),
        ('asset_purchase', 'Asset Purchase'),
        ('share_purchase', 'Share Purchase'),
        ('debt_restructuring', 'Debt Restructuring'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('due_diligence', 'Due Diligence'),
        ('negotiation', 'Negotiation'),
        ('documentation', 'Documentation'),
        ('regulatory_approval', 'Regulatory Approval'),
        ('closing', 'Closing'),
        ('post_closing', 'Post-Closing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    code = models.CharField(max_length=20, default=generate_transaction_code, editable=False, unique=True)
    title = models.CharField(max_length=300)
    description = models.TextField()
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='planning')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Financial Information
    transaction_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    target_closing_date = models.DateField(null=True, blank=True)
    actual_closing_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Team
    lead_lawyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_transactions')
    team_members = models.ManyToManyField(User, related_name='transaction_teams', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_transactions')
    
    # Related entities
    primary_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='primary_transactions')
    related_cases = models.ManyToManyField(Case, related_name='transactions', blank=True)
    related_contracts = models.ManyToManyField(Contract, related_name='transactions', blank=True)
    
    # Additional fields
    is_confidential = models.BooleanField(default=True)
    regulatory_approvals_required = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('view_confidential_transaction', 'Can view confidential transactions'),
            ('manage_transaction_team', 'Can manage transaction team'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    @property
    def is_active(self):
        return self.status not in ['completed', 'cancelled']
    
    @property
    def days_to_closing(self):
        if self.target_closing_date:
            delta = self.target_closing_date - timezone.now().date()
            return delta.days
        return None

class TransactionEntity(models.Model):
    """Entities involved in the transaction (companies, subsidiaries, etc.)"""
    ENTITY_ROLES = [
        ('acquirer', 'Acquirer'),
        ('target', 'Target'),
        ('subsidiary', 'Subsidiary'),
        ('parent', 'Parent Company'),
        ('joint_venture_partner', 'Joint Venture Partner'),
        ('lender', 'Lender'),
        ('borrower', 'Borrower'),
        ('guarantor', 'Guarantor'),
        ('advisor', 'Advisor'),
        ('other', 'Other'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='entities')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='transaction_roles')
    role = models.CharField(max_length=30, choices=ENTITY_ROLES)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['transaction', 'client', 'role']
    
    def __str__(self):
        return f"{self.client.name} - {self.get_role_display()} in {self.transaction.code}"

class EntityOwnershipHistory(models.Model):
    """Track ownership changes throughout the transaction"""
    entity = models.ForeignKey(TransactionEntity, on_delete=models.CASCADE, related_name='ownership_history')
    previous_ownership = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    new_ownership = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    change_date = models.DateTimeField(auto_now_add=True)
    change_reason = models.TextField()
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-change_date']
    
    def __str__(self):
        return f"{self.entity.client.name} ownership change on {self.change_date.date()}"

class TransactionDocument(models.Model):
    """Document management with version control and role-based access"""
    DOCUMENT_TYPES = [
        ('due_diligence', 'Due Diligence'),
        ('financial_statement', 'Financial Statement'),
        ('legal_opinion', 'Legal Opinion'),
        ('contract', 'Contract'),
        ('regulatory_filing', 'Regulatory Filing'),
        ('board_resolution', 'Board Resolution'),
        ('shareholder_agreement', 'Shareholder Agreement'),
        ('disclosure_schedule', 'Disclosure Schedule'),
        ('closing_document', 'Closing Document'),
        ('post_closing', 'Post-Closing Document'),
        ('other', 'Other'),
    ]
    
    ACCESS_LEVELS = [
        ('public', 'Public'),
        ('team_only', 'Team Only'),
        ('lead_only', 'Lead Lawyer Only'),
        ('confidential', 'Confidential'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVELS, default='team_only')
    
    # File management
    document_file = models.FileField(
        upload_to='transactions/documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'])]
    )
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_hash = models.CharField(max_length=64, blank=True)  # For integrity checking
    
    # Version control
    version = models.PositiveIntegerField(default=1)
    parent_document = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='versions')
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Due diligence tagging
    due_diligence_categories = models.ManyToManyField('DueDiligenceCategory', blank=True)
    
    # Review status
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_documents')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        permissions = [
            ('access_confidential_documents', 'Can access confidential documents'),
        ]
    
    def __str__(self):
        return f"{self.title} (v{self.version}) - {self.transaction.code}"

class DueDiligenceCategory(models.Model):
    """Categories for organizing due diligence documents"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Due Diligence Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TransactionWorkflow(models.Model):
    """Workflow templates for different transaction types"""
    name = models.CharField(max_length=200)
    transaction_type = models.CharField(max_length=50, choices=Transaction.TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    is_template = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['transaction_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_transaction_type_display()})"

class TransactionTask(models.Model):
    """Tasks and checklists for transaction workflows"""
    TASK_TYPES = [
        ('due_diligence', 'Due Diligence'),
        ('approval', 'Approval'),
        ('filing', 'Regulatory Filing'),
        ('documentation', 'Documentation'),
        ('closing', 'Closing'),
        ('post_closing', 'Post-Closing'),
        ('milestone', 'Milestone'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='tasks')
    workflow = models.ForeignKey(TransactionWorkflow, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_transaction_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_transaction_tasks')
    
    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Dependencies
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependent_tasks')
    
    # Progress tracking
    progress_percentage = models.PositiveIntegerField(default=0)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['due_date', 'priority', 'created_at']
    
    def __str__(self):
        return f"{self.title} - {self.transaction.code}"
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False

class TransactionAuditLog(models.Model):
    """Comprehensive audit trail for all transaction activities"""
    ACTION_TYPES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
        ('upload', 'Uploaded'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('assign', 'Assigned'),
        ('complete', 'Completed'),
        ('comment', 'Commented'),
        ('status_change', 'Status Changed'),
        ('other', 'Other'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    object_type = models.CharField(max_length=50)  # e.g., 'document', 'task', 'entity'
    object_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    
    # Technical details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Additional context
    old_values = models.JSONField(null=True, blank=True)  # Store previous state
    new_values = models.JSONField(null=True, blank=True)  # Store new state
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['transaction', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.get_action_type_display()} {self.object_type} in {self.transaction.code}"

class TransactionReport(models.Model):
    """Generated reports for transactions"""
    REPORT_TYPES = [
        ('status', 'Status Report'),
        ('due_diligence', 'Due Diligence Report'),
        ('financial', 'Financial Summary'),
        ('risk_assessment', 'Risk Assessment'),
        ('compliance', 'Compliance Report'),
        ('closing', 'Closing Report'),
        ('post_closing', 'Post-Closing Report'),
        ('audit', 'Audit Report'),
        ('custom', 'Custom Report'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    
    # Report content
    report_data = models.JSONField()  # Store structured report data
    report_file = models.FileField(
        upload_to='transactions/reports/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx'])],
        null=True,
        blank=True
    )
    
    # Generation details
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField(null=True, blank=True)  # Store report parameters
    
    # Access control
    is_confidential = models.BooleanField(default=True)
    shared_with = models.ManyToManyField(User, related_name='accessible_reports', blank=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.transaction.code}"

class ContractReassignment(models.Model):
    """Track contract reassignments during transactions"""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='contract_reassignments')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='reassignments')
    
    # Original assignment
    original_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='original_contracts')
    original_lawyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='original_contract_assignments')
    
    # New assignment
    new_client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reassigned_contracts')
    new_lawyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='new_contract_assignments')
    
    # Reassignment details
    reassignment_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_reassignments')
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-reassignment_date']
    
    def __str__(self):
        return f"{self.contract.title} reassigned from {self.original_client.name} to {self.new_client.name}"
