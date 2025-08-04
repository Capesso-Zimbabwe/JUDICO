from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Payment, Expense, Account, JournalEntry, JournalEntryLine

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
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit', 'credit']
        widgets = {
            'debit': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'credit': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
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