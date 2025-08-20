from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    Transaction, TransactionEntity, EntityOwnershipHistory, 
    TransactionDocument, DueDiligenceCategory, TransactionWorkflow,
    TransactionTask, TransactionAuditLog, TransactionReport, ContractReassignment
)
from client_management.models import Client
from contract_management.models import Contract
from lawyer_portal.models import LawyerProfile


class TransactionForm(forms.ModelForm):
    """Form for creating and updating transactions"""
    
    class Meta:
        model = Transaction
        fields = [
            'title', 'description', 'transaction_type', 'status', 'priority',
            'transaction_value', 'currency', 'target_closing_date',
            'lead_lawyer', 'primary_client', 'is_confidential'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Detailed description of the transaction'}),
            'target_closing_date': forms.DateInput(attrs={'type': 'date'}),
            'transaction_value': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'title': forms.TextInput(attrs={'placeholder': 'Transaction Title'}),
        }
        labels = {
            'transaction_value': 'Transaction Value',
            'target_closing_date': 'Target Closing Date',
            'lead_lawyer': 'Lead Lawyer',
            'primary_client': 'Primary Client',
            'is_confidential': 'Confidential Transaction'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lead_lawyer'].queryset = User.objects.filter(is_active=True)
        self.fields['primary_client'].queryset = Client.objects.filter(is_active=True)


class TransactionFilterForm(forms.Form):
    """Form for filtering transactions"""
    
    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'search',
            'placeholder': 'Search transactions...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), 
        required=False
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Transaction.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )
    
    transaction_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Transaction.TRANSACTION_TYPES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Transaction.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )


class TransactionEntityForm(forms.ModelForm):
    """Form for managing transaction entities"""
    
    class Meta:
        model = TransactionEntity
        fields = [
            'client', 'role', 'ownership_percentage', 'notes'
        ]
        widgets = {
            'ownership_percentage': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.00'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional notes about this entity'}),
        }
        labels = {
            'client': 'Entity/Client',
            'role': 'Role in Transaction',
            'ownership_percentage': 'Ownership Percentage (%)',
            'notes': 'Notes'
        }
    
    def __init__(self, *args, **kwargs):
        transaction = kwargs.pop('transaction', None)
        super().__init__(*args, **kwargs)
        if transaction:
            # Filter clients to exclude those already in this transaction
            existing_entities = TransactionEntity.objects.filter(transaction=transaction).values_list('client_id', flat=True)
            self.fields['client'].queryset = Client.objects.exclude(id__in=existing_entities)


class EntityOwnershipHistoryForm(forms.ModelForm):
    """Form for tracking entity ownership changes"""
    
    class Meta:
        model = EntityOwnershipHistory
        fields = [
            'previous_ownership', 'new_ownership', 'change_reason'
        ]
        widgets = {
            'previous_ownership': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.00'}),
            'new_ownership': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.00'}),
            'change_reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Reason for ownership change'}),
        }
        labels = {
            'previous_ownership': 'Previous Ownership (%)',
            'new_ownership': 'New Ownership (%)',
            'change_reason': 'Reason for Change'
        }


class TransactionDocumentForm(forms.ModelForm):
    """Form for document upload and management"""
    
    class Meta:
        model = TransactionDocument
        fields = [
            'title', 'description', 'document_file', 'document_type', 
            'access_level', 'due_diligence_categories'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Document Title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Document description'}),
            'document_file': forms.ClearableFileInput(attrs={'multiple': False}),
        }
        labels = {
            'document_file': 'Document File',
            'due_diligence_categories': 'Due Diligence Categories'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['due_diligence_category'].queryset = DueDiligenceCategory.objects.filter(is_active=True)


class DueDiligenceCategoryForm(forms.ModelForm):
    """Form for managing due diligence categories"""
    
    class Meta:
        model = DueDiligenceCategory
        fields = ['name', 'description', 'parent_category', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Category description'}),
            'name': forms.TextInput(attrs={'placeholder': 'Category Name'}),
        }
        labels = {
            'parent_category': 'Parent Category',
            'is_active': 'Active Category'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent circular parent relationships
        if self.instance.pk:
            self.fields['parent_category'].queryset = DueDiligenceCategory.objects.exclude(pk=self.instance.pk)


class TransactionWorkflowForm(forms.ModelForm):
    """Form for creating transaction workflows"""
    
    class Meta:
        model = TransactionWorkflow
        fields = [
            'name', 'description', 'transaction_type', 'is_template', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Workflow description'}),
            'name': forms.TextInput(attrs={'placeholder': 'Workflow Name'}),
        }
        labels = {
            'is_template': 'Template Workflow',
            'is_active': 'Active Workflow'
        }


class TransactionTaskForm(forms.ModelForm):
    """Form for creating and updating transaction tasks"""
    
    class Meta:
        model = TransactionTask
        fields = [
            'title', 'description', 'task_type', 'status', 'priority',
            'assigned_to', 'due_date', 'estimated_hours', 'depends_on'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Task description'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'estimated_hours': forms.NumberInput(attrs={'step': '0.25', 'min': '0'}),
            'title': forms.TextInput(attrs={'placeholder': 'Task Title'}),
        }

    def __init__(self, *args, **kwargs):
        transaction = kwargs.pop('transaction', None)
        super().__init__(*args, **kwargs)
        
        if transaction:
            # Filter depends_on to only show tasks from the same transaction
            self.fields['depends_on'].queryset = TransactionTask.objects.filter(
                workflow__transaction=transaction
            ).exclude(pk=self.instance.pk if self.instance.pk else None)


class TransactionReportForm(forms.ModelForm):
    """Form for generating transaction reports"""
    
    class Meta:
        model = TransactionReport
        fields = [
            'title', 'report_type', 'description', 'is_confidential'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Report description'}),
            'title': forms.TextInput(attrs={'placeholder': 'Report Title'}),
        }
        labels = {
            'is_confidential': 'Confidential Report'
        }


class ContractReassignmentForm(forms.ModelForm):
    """Form for contract reassignment during transactions"""
    
    class Meta:
        model = ContractReassignment
        fields = [
            'contract', 'original_client', 'original_lawyer', 
            'new_client', 'new_lawyer', 'reason', 'notes'
        ]
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Reason for reassignment'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional notes'}),
        }
        labels = {
            'original_client': 'Original Client',
            'original_lawyer': 'Original Lawyer',
            'new_client': 'New Client',
            'new_lawyer': 'New Lawyer'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contract'].queryset = Contract.objects.filter(status='active')


class BulkDocumentUploadForm(forms.Form):
    """Form for document upload"""
    
    document = forms.FileField(
        widget=forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.txt,.jpg,.png'}),
        help_text='Select a document to upload'
    )
    category = forms.ModelChoiceField(
        queryset=DueDiligenceCategory.objects.filter(is_active=True),
        required=False,
        help_text='Optional: Assign all documents to this category'
    )
    access_level = forms.ChoiceField(
        choices=TransactionDocument.ACCESS_LEVELS,
        initial='internal',
        help_text='Access level for all uploaded documents'
    )
    is_confidential = forms.BooleanField(
        required=False,
        help_text='Mark all documents as confidential'
    )