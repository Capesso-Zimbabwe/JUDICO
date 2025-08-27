from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Payment, Expense, Account, JournalEntry, JournalEntryLine, PettyCash, Report

class AccountFilterForm(forms.Form):
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search accounts...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type', 'parent_account', 'status', 'balance', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'balance': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-sm'
            }),
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
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search expenses...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'title', 'description', 'amount', 'category', 'expense_date',
            'case_number', 'matter_type',
            'account', 'tax_amount', 'tax_rate',
            'approval_level', 'billable_status', 'billable_amount',
            'invoice_number', 'vendor_name', 'vendor_tax_id',
            'receipt', 'supporting_documents', 'compliance_notes'
        ]
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Detailed description of the expense...'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'tax_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00', 'placeholder': '0.00'}),
            'tax_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00', 'max': '100.00', 'placeholder': '0.00'}),
            'billable_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00', 'placeholder': '0.00'}),
            'case_number': forms.TextInput(attrs={'placeholder': 'Case number if applicable...'}),
            'matter_type': forms.TextInput(attrs={'placeholder': 'Type of legal matter...'}),
            'invoice_number': forms.TextInput(attrs={'placeholder': 'Vendor invoice number...'}),
            'vendor_name': forms.TextInput(attrs={'placeholder': 'Vendor/Supplier name...'}),
            'vendor_tax_id': forms.TextInput(attrs={'placeholder': 'Vendor tax ID...'}),
            'compliance_notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Any compliance notes or special considerations...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['title'].required = True
        self.fields['amount'].required = True
        self.fields['category'].required = True
        self.fields['expense_date'].required = True
        
        # Add help text
        self.fields['title'].help_text = 'Enter a clear, descriptive title for the expense'
        self.fields['amount'].help_text = 'Enter the total amount before tax'
        self.fields['tax_amount'].help_text = 'Enter any applicable tax amount'
        self.fields['billable_amount'].help_text = 'Enter the amount that can be billed to the client'
        
        # Customize field labels
        self.fields['case_number'].label = 'Case Number'
        self.fields['matter_type'].label = 'Matter Type'
        self.fields['billable_amount'].label = 'Billable Amount'
        self.fields['supporting_documents'].label = 'Supporting Documents'
        self.fields['compliance_notes'].label = 'Compliance Notes'
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        tax_amount = cleaned_data.get('tax_amount', 0)
        billable_amount = cleaned_data.get('billable_amount', 0)
        
        # Validate amount
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        
        # Validate tax amount
        if tax_amount and tax_amount < 0:
            raise forms.ValidationError('Tax amount cannot be negative.')
        
        # Validate billable amount
        if billable_amount and billable_amount < 0:
            raise forms.ValidationError('Billable amount cannot be negative.')
        
        if billable_amount and amount and billable_amount > amount:
            raise forms.ValidationError('Billable amount cannot exceed the total amount.')
        
        return cleaned_data
    
    def save(self, commit=True):
        expense = super().save(commit=False)
        
        # Auto-calculate net amount
        if expense.amount and expense.tax_amount:
            expense.net_amount = expense.amount - expense.tax_amount
        
        # Set billable amount based on billable status
        if expense.billable_status == 'BILLABLE':
            expense.billable_amount = expense.amount
        elif expense.billable_status == 'NON_BILLABLE':
            expense.billable_amount = 0.00
        
        if commit:
            expense.save()
        return expense

class JournalEntryFilterForm(forms.Form):
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search journal entries...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + JournalEntry.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['entry_number', 'date', 'description', 'reference', 'status']
        widgets = {
            'entry_number': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
            'reference': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
            'status': forms.Select(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
        }

class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit', 'credit']
        widgets = {
            'account': forms.Select(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
            'description': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
            'debit': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
            'credit': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-none shadow-sm focus:outline-none focus:ring-airtable-blue focus:border-airtable-blue text-sm'}),
        }

# Formset for journal entry lines
JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry, 
    JournalEntryLine, 
    form=JournalEntryLineForm,
    extra=2,
    min_num=2,
    validate_min=True,
    can_delete=True
)

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
    
    expense_category = forms.ChoiceField(
        choices=[('', 'All Categories')] + Expense.CATEGORY_CHOICES,
        required=False,
        label='Expense Category'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-generate report name if creating new record
        if not self.instance.pk:
            import datetime
            today = datetime.date.today()
            self.fields['name'].initial = f'Report {today.strftime("%Y-%m-%d")}'