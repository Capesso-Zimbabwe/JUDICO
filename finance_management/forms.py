from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    Invoice, InvoiceItem, Payment, Expense, Account, 
    JournalEntry, JournalEntryLine, PettyCash, Report,
    Journal, AccountingPeriod, AccountBalance, FinancialStatement,
    ExpenseCategory, ExpenseLineItem, AccountsPayable, AccountsPayableLineItem
)
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

class AccountFilterForm(forms.Form):
    account_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Account.ACCOUNT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    account_category = forms.ChoiceField(
        choices=[('', 'All Categories')] + Account.ACCOUNT_CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Account.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by code or name'})
    )

class AccountForm(ModelForm):
    class Meta:
        model = Account
        fields = [
            'code', 'name', 'account_type', 'account_category', 'parent_account',
            'description', 'status', 'opening_balance', 'normal_balance',
            'is_bank_account', 'is_cash_account', 'is_contra_account'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1000'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'account_category': forms.Select(attrs={'class': 'form-control'}),
            'parent_account': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'normal_balance': forms.Select(attrs={'class': 'form-control'}),
            'is_bank_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_cash_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_contra_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'client', 'issue_date', 'due_date', 'status', 
                 'subtotal', 'tax', 'total', 'notes']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'amount']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_date', 'payment_method', 
                 'reference_number', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class InvoiceFilterForm(forms.Form):
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search invoices...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)

class ExpenseFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Statuses')] + Expense.EXPENSE_STATUS_CHOICES
    EXPENSE_TYPE_CHOICES = [('', 'All Types')] + Expense.EXPENSE_TYPE_CHOICES
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search expenses...'})
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    expense_type = forms.ChoiceField(choices=EXPENSE_TYPE_CHOICES, required=False)
    expense_category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories"
    )
    period = forms.ModelChoiceField(
        queryset=AccountingPeriod.objects.all(),
        required=False,
        empty_label="All Periods"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    vendor = forms.CharField(required=False)
    min_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Min amount'})
    )
    max_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Max amount'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Start date cannot be after end date")
        
        if min_amount and max_amount and min_amount > max_amount:
            raise forms.ValidationError("Minimum amount cannot be greater than maximum amount")
        
        return cleaned_data


class ExpenseApprovalForm(forms.Form):
    approval_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional approval notes...'})
    )
    
    def __init__(self, *args, **kwargs):
        expense = kwargs.pop('expense', None)
        super().__init__(*args, **kwargs)
        if expense:
            self.fields['approval_notes'].initial = f"Approved expense: {expense.title}"


class ExpensePaymentForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CHECK', 'Check'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('WIRE_TRANSFER', 'Wire Transfer'),
        ('OTHER', 'Other'),
    ]
    
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES)
    payment_reference = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Check number, transaction ID, etc.'})
    )
    payment_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional payment notes...'})
    )
    
    def __init__(self, *args, **kwargs):
        expense = kwargs.pop('expense', None)
        super().__init__(*args, **kwargs)
        if expense:
            self.fields['payment_reference'].initial = f"Payment for {expense.reference_number}"


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'title', 'description', 'expense_type', 'expense_date', 'due_date',
            'vendor', 'expense_category', 'period', 'total_amount', 'tax_amount',
            'payment_method', 'payment_reference'
        ]
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'total_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00'}),
            'tax_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active expense categories
        self.fields['expense_category'].queryset = ExpenseCategory.objects.filter(is_active=True)
        self.fields['expense_category'].empty_label = "Select expense category"
        
        # Only show open periods
        self.fields['period'].queryset = AccountingPeriod.objects.filter(status='OPEN')
        self.fields['period'].empty_label = "Select accounting period"
    
    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get('total_amount')
        tax_amount = cleaned_data.get('tax_amount')
        
        if total_amount and total_amount <= 0:
            raise forms.ValidationError("Total amount must be greater than 0")
        
        if tax_amount and tax_amount < 0:
            raise forms.ValidationError("Tax amount cannot be negative")
        
        if total_amount and tax_amount and tax_amount > total_amount:
            raise forms.ValidationError("Tax amount cannot exceed total amount")
        
        return cleaned_data
    

class ExpenseLineItemForm(forms.ModelForm):
    class Meta:
        model = ExpenseLineItem
        fields = ['description', 'quantity', 'unit_price', 'tax_rate']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Item description'}),
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00'}),
            'tax_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00', 'max': '100.00'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        
        if quantity and unit_price:
            if quantity <= 0:
                raise forms.ValidationError("Quantity must be greater than 0")
            if unit_price < 0:
                raise forms.ValidationError("Unit price cannot be negative")
        
        return cleaned_data


ExpenseLineItemFormSet = forms.inlineformset_factory(
    Expense, 
    ExpenseLineItem, 
    form=ExpenseLineItemForm,
    extra=1,
    can_delete=True,
    fields=['description', 'quantity', 'unit_price', 'tax_rate']
)


class JournalForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['code', 'name', 'journal_type', 'description', 'status']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., GJ'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'journal_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class AccountingPeriodForm(ModelForm):
    class Meta:
        model = AccountingPeriod
        fields = ['name', 'start_date', 'end_date', 'is_current', 'is_adjustment_period']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., January 2024'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_adjustment_period': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class JournalEntryForm(ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['journal', 'date', 'description', 'reference', 'period']
        widgets = {
            'journal': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'period': forms.Select(attrs={'class': 'form-control'}),
        }

class JournalEntryLineForm(ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit', 'credit']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control debit-amount', 'step': '0.01', 'min': '0'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control credit-amount', 'step': '0.01', 'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit') or Decimal('0.00')
        credit = cleaned_data.get('credit') or Decimal('0.00')
        
        if debit > 0 and credit > 0:
            raise forms.ValidationError("A line cannot have both debit and credit amounts.")
        
        if debit == 0 and credit == 0:
            raise forms.ValidationError("A line must have either a debit or credit amount.")
        
        return cleaned_data

JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry, JournalEntryLine,
    form=JournalEntryLineForm,
    extra=2,
    can_delete=True,
    min_num=2,
    validate_min=True
)

class JournalEntryFilterForm(forms.Form):
    journal = forms.ModelChoiceField(
        queryset=Journal.objects.filter(status='ACTIVE'),
        required=False,
        empty_label="All Journals",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    period = forms.ModelChoiceField(
        queryset=AccountingPeriod.objects.all(),
        required=False,
        empty_label="All Periods",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + JournalEntry.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by description or reference'})
    )

class FinancialStatementForm(forms.Form):
    STATEMENT_TYPE_CHOICES = [
        ('TRIAL_BALANCE', 'Trial Balance'),
        ('BALANCE_SHEET', 'Balance Sheet'),
        ('INCOME_STATEMENT', 'Income Statement'),
        ('CASH_FLOW', 'Statement of Cash Flows'),
    ]
    
    statement_type = forms.ChoiceField(
        choices=STATEMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    period = forms.ModelChoiceField(
        queryset=AccountingPeriod.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    as_of_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    format = forms.ChoiceField(
        choices=[('HTML', 'HTML'), ('PDF', 'PDF'), ('EXCEL', 'Excel'), ('CSV', 'CSV')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class PeriodClosingForm(forms.Form):
    period = forms.ModelChoiceField(
        queryset=AccountingPeriod.objects.filter(status='OPEN'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    closing_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Optional notes about the period closing'})
    )
    create_reversing_entries = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Create reversing entries for next period"
    )

class AccountBalanceForm(forms.ModelForm):
    class Meta:
        model = AccountBalance
        fields = ['account', 'period', 'opening_balance', 'period_debits', 'period_credits', 'closing_balance']
        widgets = {
            'opening_balance': forms.NumberInput(attrs={'step': '0.01'}),
            'period_debits': forms.NumberInput(attrs={'step': '0.01'}),
            'period_credits': forms.NumberInput(attrs={'step': '0.01'}),
            'closing_balance': forms.NumberInput(attrs={'step': '0.01'}),
        }


# Expense Management Forms
class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description', 'account', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show expense accounts
        self.fields['account'].queryset = Account.objects.filter(account_type='EXPENSE', is_active=True)
        self.fields['account'].empty_label = "Select an expense account"


class PettyCashFilterForm(forms.Form):
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search petty cash...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + PettyCash.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )

class PettyCashForm(forms.ModelForm):
    class Meta:
        model = PettyCash
        fields = ['transaction_number', 'transaction_type', 'description', 'amount', 
                 'transaction_date', 'recipient', 'purpose', 'receipt', 'status']
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date'}),
            'purpose': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-generate transaction number if creating new record
        if not self.instance.pk:
            import datetime
            today = datetime.date.today()
            count = PettyCash.objects.filter(transaction_date=today).count() + 1
            self.fields['transaction_number'].initial = f'PC-{today.strftime("%Y%m%d")}-{count:03d}'

class ReportFilterForm(forms.Form):
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search reports...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)
    report_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Report.REPORT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Report.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )
    format = forms.ChoiceField(
        choices=[('', 'All Formats')] + Report.FORMAT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['name', 'report_type', 'start_date', 'end_date', 'format', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    # Additional filter fields that will be shown conditionally
    petty_cash_status = forms.ChoiceField(
        choices=[('', 'All Status')] + PettyCash.STATUS_CHOICES,
        required=False,
        label='Transaction Status'
    )
    
    expense_category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        label='Expense Category'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-generate report name if creating new record
        if not self.instance.pk:
            import datetime
            today = datetime.date.today()
            self.fields['name'].initial = f'Report {today.strftime("%Y-%m-%d")}'

class AccountsPayableForm(forms.ModelForm):
    """Form for creating and editing Accounts Payable"""
    
    class Meta:
        model = AccountsPayable
        fields = [
            'vendor', 'vendor_invoice_number', 'invoice_date', 'due_date', 
            'payment_terms', 'subtotal', 'tax_amount', 'total_amount',
            'expense_category', 'period', 'description', 'notes', 'is_recurring',
            'recurring_frequency', 'attachments'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active expense categories only
        self.fields['expense_category'].queryset = ExpenseCategory.objects.filter(is_active=True)
        
        # Filter open accounting periods only
        self.fields['period'].queryset = AccountingPeriod.objects.filter(status='OPEN')
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            else:
                field.widget.attrs['class'] = 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
    
    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get('invoice_date')
        due_date = cleaned_data.get('due_date')
        subtotal = cleaned_data.get('subtotal')
        tax_amount = cleaned_data.get('tax_amount')
        total_amount = cleaned_data.get('total_amount')
        
        # Validate dates
        if invoice_date and due_date and invoice_date > due_date:
            raise forms.ValidationError("Due date cannot be before invoice date")
        
        # Validate amounts
        if subtotal and tax_amount and total_amount:
            calculated_total = subtotal + tax_amount
            if abs(calculated_total - total_amount) > Decimal('0.01'):
                raise forms.ValidationError(f"Total amount should be {calculated_total} (subtotal + tax)")
        
        return cleaned_data

class AccountsPayableLineItemForm(forms.ModelForm):
    """Form for individual line items in accounts payable"""
    
    class Meta:
        model = AccountsPayableLineItem
        fields = ['description', 'quantity', 'unit_price', 'tax_rate', 'expense_account']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Item description'}),
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'tax_rate': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter expense accounts only
        self.fields['expense_account'].queryset = Account.objects.filter(
            account_type='EXPENSE',
            status='ACTIVE'
        )
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            else:
                field.widget.attrs['class'] = 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'

# Create formset for line items
AccountsPayableLineItemFormSet = forms.inlineformset_factory(
    AccountsPayable,
    AccountsPayableLineItem,
    form=AccountsPayableLineItemForm,
    extra=1,
    can_delete=True,
    fields=['description', 'quantity', 'unit_price', 'tax_rate', 'expense_account']
)

class AccountsPayableFilterForm(forms.Form):
    """Form for filtering accounts payable"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search vendors, invoice numbers...',
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + AccountsPayable.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
        })
    )
    
    vendor = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Filter by vendor...',
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
        })
    )
    
    expense_category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
        })
    )

class AccountsPayableApprovalForm(forms.ModelForm):
    """Form for approving accounts payable"""
    
    class Meta:
        model = AccountsPayable
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            })
        }

class AccountsPayablePaymentForm(forms.ModelForm):
    """Form for recording payments against accounts payable"""
    
    payment_amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
        })
    )
    
    class Meta:
        model = AccountsPayable
        fields = ['payment_method', 'payment_reference']
        widgets = {
            'payment_method': forms.TextInput(attrs={
                'placeholder': 'e.g., Bank Transfer, Check, Credit Card',
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            }),
            'payment_reference': forms.TextInput(attrs={
                'placeholder': 'e.g., Check #1234, Transaction ID',
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5'
            }),
        }
    
    def clean_payment_amount(self):
        payment_amount = self.cleaned_data['payment_amount']
        instance = self.instance
        
        if instance and payment_amount > instance.balance_due:
            raise forms.ValidationError(
                f"Payment amount cannot exceed balance due (${instance.balance_due})"
            )
        
        return payment_amount