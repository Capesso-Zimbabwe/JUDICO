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
        fields = ['code', 'name', 'account_type', 'parent_account', 'status', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
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
        fields = ['title', 'description', 'amount', 'category', 'expense_date', 
                 'receipt']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

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