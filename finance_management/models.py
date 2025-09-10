from django.db import models
from django.utils import timezone
from client_management.models import Client
from django.contrib.auth.models import User
from decimal import Decimal
import uuid

class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expense'),
    ]
    
    ACCOUNT_CATEGORY_CHOICES = [
        # Assets
        ('CURRENT_ASSET', 'Current Asset'),
        ('FIXED_ASSET', 'Fixed Asset'),
        ('INTANGIBLE_ASSET', 'Intangible Asset'),
        ('INVESTMENT', 'Investment'),
        
        # Liabilities
        ('CURRENT_LIABILITY', 'Current Liability'),
        ('LONG_TERM_LIABILITY', 'Long Term Liability'),
        
        # Equity
        ('OWNERS_EQUITY', 'Owner\'s Equity'),
        ('RETAINED_EARNINGS', 'Retained Earnings'),
        
        # Revenue
        ('OPERATING_REVENUE', 'Operating Revenue'),
        ('NON_OPERATING_REVENUE', 'Non-Operating Revenue'),
        
        # Expenses
        ('OPERATING_EXPENSE', 'Operating Expense'),
        ('NON_OPERATING_EXPENSE', 'Non-Operating Expense'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('CLOSED', 'Closed'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    account_category = models.CharField(max_length=30, choices=ACCOUNT_CATEGORY_CHOICES)
    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Balance tracking
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Normal balance side
    normal_balance = models.CharField(max_length=10, choices=[('DEBIT', 'Debit'), ('CREDIT', 'Credit')])
    
    # Account properties
    is_bank_account = models.BooleanField(default=False)
    is_cash_account = models.BooleanField(default=False)
    is_contra_account = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        verbose_name_plural = 'Accounts'
    
    def __str__(self):
        return f'{self.code} - {self.name}'
    
    @property
    def balance(self):
        """Get the current balance based on normal balance side"""
        if self.normal_balance == 'DEBIT':
            return self.current_balance
        else:
            return -self.current_balance
    
    @property
    def formatted_balance(self):
        """Format balance with proper sign"""
        balance = self.balance
        if balance >= 0:
            return f"${balance:,.2f}"
        else:
            return f"(${abs(balance):,.2f})"
    
    def get_balance_as_of_date(self, as_of_date):
        """Get account balance as of a specific date"""
        from .models import JournalEntryLine
        
        # Get all journal entry lines up to the date
        lines = JournalEntryLine.objects.filter(
            account=self,
            journal_entry__date__lte=as_of_date,
            journal_entry__status='POSTED'
        )
        
        # Calculate balance
        total_debit = lines.aggregate(total=models.Sum('debit'))['total'] or Decimal('0.00')
        total_credit = lines.aggregate(total=models.Sum('credit'))['total'] or Decimal('0.00')
        
        # Add opening balance
        balance = self.opening_balance + total_debit - total_credit
        
        # Adjust for normal balance side
        if self.normal_balance == 'CREDIT':
            balance = -balance
            
        return balance

class Journal(models.Model):
    JOURNAL_TYPE_CHOICES = [
        ('GENERAL', 'General Journal'),
        ('SALES', 'Sales Journal'),
        ('PURCHASE', 'Purchase Journal'),
        ('CASH_RECEIPTS', 'Cash Receipts Journal'),
        ('CASH_DISBURSEMENTS', 'Cash Disbursements Journal'),
        ('ADJUSTING', 'Adjusting Journal'),
        ('CLOSING', 'Closing Journal'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('CLOSED', 'Closed'),
    ]
    
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    journal_type = models.CharField(max_length=20, choices=JOURNAL_TYPE_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    next_number = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        verbose_name_plural = 'Journals'
    
    def __str__(self):
        return f'{self.code} - {self.name}'
    
    def get_next_entry_number(self):
        """Get the next available entry number for this journal"""
        return f"{self.code}-{self.next_number:06d}"

class AccountingPeriod(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('LOCKED', 'Locked'),
    ]
    
    name = models.CharField(max_length=100)  # e.g., "January 2024"
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    is_current = models.BooleanField(default=False)
    is_adjustment_period = models.BooleanField(default=False)
    
    # Period balances
    opening_equity = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    closing_equity = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Closing information
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closing_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Accounting Periods'
        unique_together = ['start_date', 'end_date']
    
    def __str__(self):
        return f'{self.name} ({self.start_date} - {self.end_date})'
    
    @property
    def is_closable(self):
        """Check if period can be closed"""
        return self.status == 'OPEN' and not self.is_current
    
    def close_period(self, closed_by_user, notes=""):
        """Close the accounting period"""
        if not self.is_closable:
            raise ValueError("Period cannot be closed")
        
        self.status = 'CLOSED'
        self.closed_by = closed_by_user
        self.closed_at = timezone.now()
        self.closing_notes = notes
        self.save()
        
        # Create closing entries
        self.create_closing_entries()
    
    def create_closing_entries(self):
        """Create closing entries for revenue and expense accounts"""
        from .models import JournalEntry, JournalEntryLine
        
        # Get revenue and expense accounts
        revenue_accounts = Account.objects.filter(account_type='REVENUE', status='ACTIVE')
        expense_accounts = Account.objects.filter(account_type='EXPENSE', status='ACTIVE')
        
        # Calculate totals
        total_revenue = sum(acc.get_balance_as_of_date(self.end_date) for acc in revenue_accounts)
        total_expenses = sum(acc.get_balance_as_of_date(self.end_date) for acc in expense_accounts)
        net_income = total_revenue - total_expenses
        
        # Create closing journal entry
        closing_je = JournalEntry.objects.create(
            journal=Journal.objects.get(code='CLOSING'),
            entry_number=f"CLOSE-{self.name.replace(' ', '-')}",
            date=self.end_date,
            description=f"Closing entries for {self.name}",
            reference=f"PERIOD-{self.id}",
            status='POSTED',
            created_by=self.closed_by
        )
        
        # Close revenue accounts
        for account in revenue_accounts:
            balance = account.get_balance_as_of_date(self.end_date)
            if balance != 0:
                JournalEntryLine.objects.create(
                    journal_entry=closing_je,
                    account=account,
                    description=f"Close {account.name}",
                    debit=balance,
                    credit=0.00
                )
        
        # Close expense accounts
        for account in expense_accounts:
            balance = account.get_balance_as_of_date(self.end_date)
            if balance != 0:
                JournalEntryLine.objects.create(
                    journal_entry=closing_je,
                    account=account,
                    description=f"Close {account.name}",
                    debit=0.00,
                    credit=balance
                )
        
        # Close to retained earnings
        retained_earnings = Account.objects.filter(code='3000').first()  # Assuming 3000 is retained earnings
        if retained_earnings:
            JournalEntryLine.objects.create(
                journal_entry=closing_je,
                account=retained_earnings,
                description=f"Net income for {self.name}",
                debit=0.00 if net_income >= 0 else abs(net_income),
                credit=net_income if net_income >= 0 else 0.00
            )

class JournalEntry(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('REVERSED', 'Reversed'),
        ('VOID', 'Void'),
    ]
    
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='entries')
    entry_number = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Period information
    period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE, related_name='journal_entries')
    
    # Totals
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_entries')
    posted_at = models.DateTimeField(null=True, blank=True)
    
    # Reversal information
    reversed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reversed_entries')
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversal_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Journal Entries'
    
    def __str__(self):
        return f'{self.entry_number} - {self.description[:50]}'
    
    def is_balanced(self):
        """Check if debits equal credits"""
        return self.total_debit == self.total_credit
    
    def post_entry(self, posted_by_user):
        """Post the journal entry"""
        if self.status != 'DRAFT':
            raise ValueError("Only draft entries can be posted")
        
        if not self.is_balanced():
            raise ValueError("Entry must be balanced before posting")
        
        self.status = 'POSTED'
        self.posted_by = posted_by_user
        self.posted_at = timezone.now()
        self.save()
        
        # Update account balances
        self.update_account_balances()
    
    def update_account_balances(self):
        """Update account balances when entry is posted"""
        for line in self.lines.all():
            account = line.account
            
            if line.debit > 0:
                if account.normal_balance == 'DEBIT':
                    account.current_balance += line.debit
                else:
                    account.current_balance -= line.debit
            else:
                if account.normal_balance == 'DEBIT':
                    account.current_balance -= line.credit
                else:
                    account.current_balance += line.credit
            
            account.save()
    
    def reverse_entry(self, reversed_by_user, reason=""):
        """Reverse the journal entry"""
        if self.status != 'POSTED':
            raise ValueError("Only posted entries can be reversed")
        
        # Create reversing entry
        reversing_je = JournalEntry.objects.create(
            journal=self.journal,
            entry_number=f"REV-{self.entry_number}",
            date=timezone.now().date(),
            description=f"Reversal of {self.entry_number}",
            reference=f"REV-{self.reference}",
            status='POSTED',
            period=self.period,
            created_by=reversed_by_user
        )
        
        # Create reversing lines
        for line in self.lines.all():
            JournalEntryLine.objects.create(
                journal_entry=reversing_je,
                account=line.account,
                description=f"Reverse {line.description}",
                debit=line.credit,
                credit=line.debit
            )
        
        # Mark original as reversed
        self.status = 'REVERSED'
        self.reversed_by = reversed_by_user
        self.reversed_at = timezone.now()
        self.reversal_reason = reason
        self.save()
        
        return reversing_je

class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='journal_lines')
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Line properties
    is_adjustment = models.BooleanField(default=False)
    is_closing = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
        verbose_name_plural = 'Journal Entry Lines'
    
    def __str__(self):
        return f'{self.journal_entry.entry_number} - {self.account.code}'
    
    @property
    def amount(self):
        """Get the amount (debit or credit)"""
        return self.debit if self.debit > 0 else self.credit
    
    @property
    def side(self):
        """Get the side (debit or credit)"""
        return 'DEBIT' if self.debit > 0 else 'CREDIT'

class AccountBalance(models.Model):
    """Track account balances over time"""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='balances')
    period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE, related_name='account_balances')
    
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    period_debits = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    period_credits = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['account', 'period']
        ordering = ['account__code', 'period__start_date']
        verbose_name_plural = 'Account Balances'
    
    def __str__(self):
        return f'{self.account.code} - {self.period.name}'
    
    @property
    def net_movement(self):
        """Net movement during the period"""
        return self.period_debits - self.period_credits
    
    def calculate_closing_balance(self):
        """Calculate closing balance"""
        self.closing_balance = self.opening_balance + self.net_movement
        self.save()

class FinancialStatement(models.Model):
    """Generated financial statements"""
    STATEMENT_TYPE_CHOICES = [
        ('TRIAL_BALANCE', 'Trial Balance'),
        ('BALANCE_SHEET', 'Balance Sheet'),
        ('INCOME_STATEMENT', 'Income Statement'),
    ]
    
    FORMAT_CHOICES = [
        ('HTML', 'HTML'),
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
    ]
    
    statement_type = models.CharField(max_length=20, choices=STATEMENT_TYPE_CHOICES)
    period = models.ForeignKey(AccountingPeriod, on_delete=models.CASCADE, null=True, blank=True)
    as_of_date = models.DateField()
    data = models.JSONField()
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='HTML')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.get_statement_type_display()} - {self.as_of_date}"


# Expense Management Models
class ExpenseCategory(models.Model):
    """Categories for organizing expenses"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, limit_choices_to={'account_type': 'EXPENSE'})
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Expense Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """Main expense record"""
    EXPENSE_STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    EXPENSE_TYPE_CHOICES = [
        ('OPERATING', 'Operating Expense'),
        ('CAPITAL', 'Capital Expense'),
        ('PREPAID', 'Prepaid Expense'),
        ('ACCRUED', 'Accrued Expense'),
    ]
    
    reference_number = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='OPERATING')
    status = models.CharField(max_length=20, choices=EXPENSE_STATUS_CHOICES, default='DRAFT')
    
    # Financial Details
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Dates
    expense_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    
    # Relationships
    vendor = models.CharField(max_length=200, blank=True)
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT, null=True, blank=True)
    
    # Payment Details
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Journal Entry Integration
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='expenses_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_approved')
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_paid')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.reference_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate net amount
        if not self.net_amount:
            self.net_amount = self.total_amount - self.tax_amount
        
        # Auto-generate reference number if not provided
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()
        
        super().save(*args, **kwargs)
    
    def generate_reference_number(self):
        """Generate unique reference number"""
        from datetime import datetime
        prefix = "EXP"
        date_part = datetime.now().strftime("%Y%m")
        
        # Get the last expense number for this month
        last_expense = Expense.objects.filter(
            reference_number__startswith=f"{prefix}{date_part}"
        ).order_by('reference_number').last()
        
        if last_expense:
            try:
                last_number = int(last_expense.reference_number[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{date_part}{new_number:04d}"
    
    def create_journal_entry(self):
        """Create journal entry for this expense"""
        if self.journal_entry:
            return self.journal_entry
        
        # Get the appropriate journal
        journal = Journal.objects.filter(code='CDJ').first()  # Cash Disbursements Journal
        
        # Create journal entry
        entry = JournalEntry.objects.create(
            journal=journal,
            period=self.period,
            entry_date=self.expense_date,
            reference=self.reference_number,
            description=f"Expense: {self.title}",
            status='DRAFT'
        )
        
        # Create journal entry lines
        # Debit the expense account
        JournalEntryLine.objects.create(
            journal_entry=entry,
            account=self.expense_category.account,
            description=self.description or self.title,
            debit_amount=self.net_amount,
            credit_amount=0
        )
        
        # Credit cash/bank account (you can make this configurable)
        cash_account = Account.objects.filter(is_cash_account=True).first()
        if cash_account:
            JournalEntryLine.objects.create(
                journal_entry=entry,
                account=cash_account,
                description=f"Payment for {self.title}",
                debit_amount=0,
                credit_amount=self.net_amount
            )
        
        # If there's tax, create tax liability entry
        if self.tax_amount > 0:
            tax_account = Account.objects.filter(name__icontains='Tax Payable').first()
            if tax_account:
                JournalEntryLine.objects.create(
                    journal_entry=entry,
                    account=tax_account,
                    description=f"Tax for {self.title}",
                    debit_amount=0,
                    credit_amount=self.tax_amount
                )
                
                # Adjust cash credit for tax
                if cash_account:
                    # Update the cash line to include tax
                    cash_line = entry.lines.filter(account=cash_account).first()
                    if cash_line:
                        cash_line.credit_amount = self.total_amount
                        cash_line.save()
        
        self.journal_entry = entry
        self.save()
        
        return entry
    
    def approve_expense(self, approved_by_user):
        """Approve the expense"""
        self.status = 'APPROVED'
        self.approved_by = approved_by_user
        self.save()
    
    def mark_as_paid(self, paid_by_user, payment_method='', payment_reference=''):
        """Mark expense as paid"""
        self.status = 'PAID'
        self.paid_by = paid_by_user
        self.paid_date = timezone.now().date()
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self.save()
        
        # Post the journal entry if not already posted
        if self.journal_entry and self.journal_entry.status == 'DRAFT':
            self.journal_entry.post_entry(paid_by_user)
    
    def get_status_display_class(self):
        """Get CSS class for status display"""
        status_classes = {
            'DRAFT': 'bg-gray-100 text-gray-800',
            'SUBMITTED': 'bg-blue-100 text-blue-800',
            'APPROVED': 'bg-green-100 text-green-800',
            'PAID': 'bg-purple-100 text-purple-800',
            'REJECTED': 'bg-red-100 text-red-800',
            'CANCELLED': 'bg-yellow-100 text-yellow-800',
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')


class ExpenseLineItem(models.Model):
    """Individual line items within an expense"""
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.expense.reference_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount and tax
        self.amount = self.quantity * self.unit_price
        self.tax_amount = self.amount * (self.tax_rate / 100)
        super().save(*args, **kwargs)

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

    @property
    def amount_paid(self):
        from django.db.models import Sum
        return self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    @property
    def outstanding_amount(self):
        outstanding = (self.total or Decimal('0.00')) - self.amount_paid
        return outstanding if outstanding > 0 else Decimal('0.00')

    @property
    def days_past_due(self):
        if self.due_date and self.outstanding_amount > 0 and self.due_date < timezone.now().date():
            return (timezone.now().date() - self.due_date).days
        return 0

    @property
    def aging_bucket(self):
        days = self.days_past_due
        if days <= 0:
            return 'Current'
        if days <= 30:
            return '1–30'
        if days <= 60:
            return '31–60'
        if days <= 90:
            return '61–90'
        return '90+'

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
        ('cash_flow', 'Cash Flow Report'),
        ('profit_loss', 'Profit & Loss Statement'),
        ('balance_sheet', 'Balance Sheet'),
        ('accounts_receivable', 'Accounts Receivable Aging'),
        ('accounts_payable', 'Accounts Payable Aging'),
        ('expense_analysis', 'Expense Analysis Report'),
        ('revenue_analysis', 'Revenue Analysis Report'),
        ('working_capital', 'Working Capital Report'),
        ('collection_performance', 'Collection Performance Report'),
        ('vendor_analysis', 'Vendor Analysis Report'),
        ('client_revenue', 'Client Revenue Report'),
        ('monthly_summary', 'Monthly Financial Summary'),
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
    report_type = models.CharField(max_length=25, choices=REPORT_TYPE_CHOICES)
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

class AccountsPayable(models.Model):
    """
    Accounts Payable - tracks what the company owes to vendors
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
        ('OVERDUE', 'Overdue'),
    ]
    
    PAYMENT_TERMS_CHOICES = [
        ('IMMEDIATE', 'Immediate'),
        ('NET_15', 'Net 15'),
        ('NET_30', 'Net 30'),
        ('NET_45', 'Net 45'),
        ('NET_60', 'Net 60'),
        ('NET_90', 'Net 90'),
        ('CUSTOM', 'Custom'),
    ]
    
    # Basic Information
    reference_number = models.CharField(max_length=50, unique=True, blank=True)
    vendor = models.CharField(max_length=255)
    vendor_invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='NET_30')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(max_length=20, blank=True)  # monthly, quarterly, etc.
    
    # Accounting Integration
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    period = models.ForeignKey(AccountingPeriod, on_delete=models.SET_NULL, null=True, blank=True)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Approval and Payment
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payables')
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='paid_payables')
    paid_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Additional Information
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    attachments = models.FileField(upload_to='payables/', blank=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_payables')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-invoice_date', '-created_at']
        verbose_name_plural = 'Accounts Payable'
    
    def __str__(self):
        return f'{self.reference_number} - {self.vendor} - ${self.total_amount}'
    
    def save(self, *args, **kwargs):
        # Auto-generate reference number if not provided
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()
        
        # Calculate balance due
        self.balance_due = self.total_amount - self.amount_paid
        
        # Update status based on balance
        if self.balance_due <= 0 and self.total_amount > 0:
            self.status = 'PAID'
        elif self.balance_due > 0 and self.due_date < timezone.now().date():
            self.status = 'OVERDUE'
        
        super().save(*args, **kwargs)
    
    def generate_reference_number(self):
        """Generate a unique reference number"""
        import uuid
        return f"AP-{timezone.now().strftime('%Y%m')}-{str(uuid.uuid4())[:8].upper()}"
    
    @property
    def is_overdue(self):
        """Check if the payable is overdue"""
        return self.due_date < timezone.now().date() and self.balance_due > 0
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0
    
    @property
    def payment_status_display(self):
        """Get human-readable payment status"""
        if self.balance_due <= 0:
            return "Paid"
        elif self.amount_paid > 0:
            return f"Partially Paid (${self.amount_paid})"
        else:
            return "Unpaid"
    
    def get_status_display_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'DRAFT': 'bg-gray-100 text-gray-800',
            'PENDING_APPROVAL': 'bg-yellow-100 text-yellow-800',
            'APPROVED': 'bg-blue-100 text-blue-800',
            'PARTIALLY_PAID': 'bg-orange-100 text-orange-800',
            'PAID': 'bg-green-100 text-green-800',
            'CANCELLED': 'bg-red-100 text-red-800',
            'OVERDUE': 'bg-red-100 text-red-800',
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')
    
    def approve(self, approved_by_user):
        """Approve the payable"""
        if self.status == 'DRAFT':
            self.status = 'APPROVED'
            self.approved_by = approved_by_user
            self.approved_at = timezone.now()
            self.save()
            return True
        return False
    
    def record_payment(self, amount, paid_by_user, payment_method="", payment_reference=""):
        """Record a payment against this payable"""
        if amount <= 0:
            return False
        
        self.amount_paid += amount
        self.paid_by = paid_by_user
        self.paid_date = timezone.now()
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        
        # Update status
        if self.amount_paid >= self.total_amount:
            self.status = 'PAID'
        elif self.amount_paid > 0:
            self.status = 'PARTIALLY_PAID'
        
        self.save()
        return True

class AccountsPayableLineItem(models.Model):
    """
    Individual line items for accounts payable invoices
    """
    payable = models.ForeignKey(AccountsPayable, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.00)  # 0.0825 for 8.25%
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Account mapping
    expense_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['id']
        verbose_name_plural = 'Accounts Payable Line Items'
    
    def __str__(self):
        return f'{self.description} - {self.quantity} x ${self.unit_price}'
    
    def save(self, *args, **kwargs):
        # Calculate line total
        subtotal = self.quantity * self.unit_price
        tax_amount = subtotal * self.tax_rate
        self.line_total = subtotal + tax_amount
        super().save(*args, **kwargs)
