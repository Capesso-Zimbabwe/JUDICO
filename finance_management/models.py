from django.db import models
from django.utils import timezone
from client_management.models import Client
from django.contrib.auth.models import User

class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expense'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f'{self.code} - {self.name}'

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled')
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Invoice {self.invoice_number} - {self.client.name}'

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.description} - {self.invoice.invoice_number}'

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHECK', 'Check'),
        ('CREDIT_CARD', 'Credit Card'),
        ('OTHER', 'Other')
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment {self.reference_number} for Invoice {self.invoice.invoice_number}'

class Expense(models.Model):
    # Legal Accounting Standard Categories
    CATEGORY_CHOICES = [
        # Office & Administrative
        ('OFFICE_SUPPLIES', 'Office Supplies'),
        ('OFFICE_EQUIPMENT', 'Office Equipment'),
        ('OFFICE_RENT', 'Office Rent'),
        ('OFFICE_MAINTENANCE', 'Office Maintenance'),
        ('OFFICE_INSURANCE', 'Office Insurance'),
        ('OFFICE_SECURITY', 'Office Security'),
        
        # Utilities & Services
        ('UTILITIES_ELECTRICITY', 'Electricity'),
        ('UTILITIES_WATER', 'Water'),
        ('UTILITIES_GAS', 'Gas'),
        ('UTILITIES_INTERNET', 'Internet & Communications'),
        ('UTILITIES_PHONE', 'Phone Services'),
        ('UTILITIES_CABLE', 'Cable & TV'),
        
        # Professional Services
        ('LEGAL_FEES', 'Legal Fees'),
        ('ACCOUNTING_FEES', 'Accounting Fees'),
        ('CONSULTING_FEES', 'Consulting Fees'),
        ('PROFESSIONAL_DEVELOPMENT', 'Professional Development'),
        ('BAR_ASSOCIATION_FEES', 'Bar Association Fees'),
        ('CONTINUING_EDUCATION', 'Continuing Legal Education'),
        
        # Client Matter Expenses
        ('COURT_FILING_FEES', 'Court Filing Fees'),
        ('PROCESS_SERVING', 'Process Serving'),
        ('EXPERT_WITNESS_FEES', 'Expert Witness Fees'),
        ('INVESTIGATION_COSTS', 'Investigation Costs'),
        ('TRAVEL_EXPENSES', 'Travel Expenses'),
        ('MEAL_EXPENSES', 'Meal Expenses'),
        ('ACCOMMODATION', 'Accommodation'),
        ('TRANSPORTATION', 'Transportation'),
        
        # Marketing & Business Development
        ('MARKETING_ADVERTISING', 'Marketing & Advertising'),
        ('BUSINESS_DEVELOPMENT', 'Business Development'),
        ('NETWORKING_EVENTS', 'Networking Events'),
        ('PUBLICATIONS', 'Publications & Subscriptions'),
        
        # Technology & Software
        ('SOFTWARE_LICENSES', 'Software Licenses'),
        ('TECHNOLOGY_MAINTENANCE', 'Technology Maintenance'),
        ('DATA_BACKUP', 'Data Backup & Security'),
        ('CLOUD_SERVICES', 'Cloud Services'),
        
        # Staff & HR
        ('STAFF_SALARIES', 'Staff Salaries'),
        ('STAFF_BENEFITS', 'Staff Benefits'),
        ('STAFF_TRAINING', 'Staff Training'),
        ('STAFF_EQUIPMENT', 'Staff Equipment'),
        
        # Compliance & Regulatory
        ('COMPLIANCE_FEES', 'Compliance Fees'),
        ('REGULATORY_FILINGS', 'Regulatory Filings'),
        ('AUDIT_FEES', 'Audit Fees'),
        ('LICENSING_FEES', 'Licensing Fees'),
        
        # Other
        ('OTHER', 'Other Expenses'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
        ('RECONCILED', 'Reconciled'),
    ]
    
    APPROVAL_LEVEL_CHOICES = [
        ('STAFF', 'Staff Level'),
        ('SUPERVISOR', 'Supervisor Level'),
        ('MANAGER', 'Manager Level'),
        ('PARTNER', 'Partner Level'),
        ('EXECUTIVE', 'Executive Level'),
    ]
    
    BILLABLE_CHOICES = [
        ('BILLABLE', 'Billable to Client'),
        ('NON_BILLABLE', 'Non-Billable'),
        ('PARTIALLY_BILLABLE', 'Partially Billable'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    expense_date = models.DateField(default=timezone.now)
    
    # Legal System Integration
    client_case = models.ForeignKey('client_management.Case', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    case_number = models.CharField(max_length=100, blank=True)
    matter_type = models.CharField(max_length=100, blank=True)
    
    # Accounting Integration
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    journal_entry = models.ForeignKey('JournalEntry', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Approval & Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    approval_level = models.CharField(max_length=20, choices=APPROVAL_LEVEL_CHOICES, default='STAFF')
    billable_status = models.CharField(max_length=20, choices=BILLABLE_CHOICES, default='NON_BILLABLE')
    billable_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Approval Chain
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_expenses')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_expenses')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_expenses')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Documentation
    receipt = models.FileField(upload_to='expenses/receipts/', blank=True)
    supporting_documents = models.FileField(upload_to='expenses/supporting_docs/', blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    vendor_name = models.CharField(max_length=255, blank=True)
    vendor_tax_id = models.CharField(max_length=50, blank=True)
    
    # Compliance & Audit
    compliance_notes = models.TextField(blank=True)
    audit_trail = models.JSONField(default=dict, blank=True)
    is_compliant = models.BooleanField(default=True)
    compliance_review_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name_plural = 'Expenses'
        indexes = [
            models.Index(fields=['expense_date']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['client_case']),
            models.Index(fields=['billable_status']),
        ]
    
    def __str__(self):
        return f'{self.title} - ${self.amount} - {self.get_status_display()}'
    
    def save(self, *args, **kwargs):
        # Calculate net amount if tax is applied
        if self.tax_amount > 0:
            self.net_amount = self.amount - self.tax_amount
        else:
            self.net_amount = self.amount
        
        # Set billable amount based on billable status
        if self.billable_status == 'BILLABLE':
            self.billable_amount = self.amount
        elif self.billable_status == 'PARTIALLY_BILLABLE':
            # This would be set manually or through form
            pass
        else:
            self.billable_amount = 0.00
        
        super().save(*args, **kwargs)
    
    @property
    def is_approved(self):
        return self.status in ['APPROVED', 'PAID', 'RECONCILED']
    
    @property
    def is_billable(self):
        return self.billable_status in ['BILLABLE', 'PARTIALLY_BILLABLE']
    
    @property
    def total_cost(self):
        return self.amount + self.tax_amount
    
    def approve(self, approved_by_user):
        self.status = 'APPROVED'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, rejected_by_user, reason):
        self.status = 'REJECTED'
        self.compliance_notes = f"Rejected by {rejected_by_user.get_full_name()}: {reason}"
        self.save()
    
    def mark_as_paid(self):
        self.status = 'PAID'
        self.save()
    
    def create_journal_entry(self):
        """Create a journal entry for this expense"""
        if not self.account:
            return None
        
        # Create journal entry
        je = JournalEntry.objects.create(
            entry_number=f"EXP-{self.id:06d}",
            date=self.expense_date,
            description=f"Expense: {self.title}",
            reference=self.invoice_number or f"EXP-{self.id}",
            status='POSTED',
            created_by=self.submitted_by
        )
        
        # Create journal entry lines
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=self.account,
            description=self.description,
            debit=self.amount,
            credit=0.00
        )
        
        # Credit cash/bank account (assuming account 1000 is cash)
        cash_account = Account.objects.filter(code='1000').first()
        if cash_account:
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=cash_account,
                description=f"Payment for {self.title}",
                debit=0.00,
                credit=self.amount
            )
        
        self.journal_entry = je
        self.save()
        
        return je

class JournalEntry(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('REVERSED', 'Reversed'),
    ]
    
    entry_number = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Journal Entries'
    
    def __str__(self):
        return f'JE-{self.entry_number} - {self.description[:50]}'
    
    def is_balanced(self):
        return self.total_debit == self.total_credit

class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='journal_lines')
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f'{self.journal_entry.entry_number} - {self.account.code}'

class PettyCash(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('DISBURSEMENT', 'Disbursement'),
        ('REPLENISHMENT', 'Replenishment'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    transaction_number = models.CharField(max_length=50, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateField(default=timezone.now)
    recipient = models.CharField(max_length=255, blank=True)
    purpose = models.TextField(blank=True)
    receipt = models.FileField(upload_to='petty_cash/receipts/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_petty_cash')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_petty_cash')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        verbose_name_plural = 'Petty Cash Transactions'
    
    def __str__(self):
        return f'{self.transaction_number} - {self.description} - ${self.amount}'

class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('petty_cash', 'Petty Cash Report'),
        ('expense', 'Expense Report'),
        ('income', 'Income Report'),
        ('account_summary', 'Account Summary'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)  # in bytes
    description = models.TextField(blank=True)
    filters = models.JSONField(default=dict, blank=True)  # Store additional filters
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='finance_generated_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Reports'
    
    def __str__(self):
        return f'{self.name} - {self.get_report_type_display()}'
    
    @property
    def date_range(self):
        return f"{self.start_date.strftime('%b %d, %Y')} - {self.end_date.strftime('%b %d, %Y')}"
    
    @property
    def file_size_formatted(self):
        if not self.file_size:
            return 'N/A'
        
        # Convert bytes to human readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
