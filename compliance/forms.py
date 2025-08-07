from django import forms
from .models import Requirement, Audit

class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = ['title', 'category', 'due_date', 'status', 'priority', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-airtable-blue focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-2 focus:ring-airtable-blue focus:border-transparent appearance-none bg-white form-field disabled:opacity-50 disabled:cursor-not-allowed',
                'required': True
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-airtable-blue focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-2 focus:ring-airtable-blue focus:border-transparent appearance-none bg-white form-field disabled:opacity-50 disabled:cursor-not-allowed'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-2 focus:ring-airtable-blue focus:border-transparent appearance-none bg-white form-field disabled:opacity-50 disabled:cursor-not-allowed'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-airtable-blue focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default status to Pending
        self.fields['status'].initial = 'Pending'
        # Make required fields have proper labels
        self.fields['title'].label = 'Title'
        self.fields['category'].label = 'Category'
        self.fields['due_date'].label = 'Due Date'
        self.fields['status'].label = 'Status'
        self.fields['priority'].label = 'Priority'
        self.fields['description'].label = 'Description'


class AuditForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = ['title', 'audit_type', 'status', 'priority', 'scheduled_date', 'completion_date', 'auditor', 'description', 'findings']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50',
                'required': True
            }),
            'audit_type': forms.Select(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white form-field disabled:opacity-50 disabled:cursor-not-allowed',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white form-field disabled:opacity-50 disabled:cursor-not-allowed'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white form-field disabled:opacity-50 disabled:cursor-not-allowed'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50',
                'required': True
            }),
            'completion_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50'
            }),
            'auditor': forms.TextInput(attrs={
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50'
            }),
            'findings': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full text-sm px-3 py-2 border border-gray-300 rounded-none focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent form-field disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values
        self.fields['status'].initial = 'Scheduled'
        self.fields['priority'].initial = 'Medium'
        # Set proper labels
        self.fields['title'].label = 'Audit Title'
        self.fields['audit_type'].label = 'Audit Type'
        self.fields['status'].label = 'Status'
        self.fields['priority'].label = 'Priority'
        self.fields['scheduled_date'].label = 'Scheduled Date'
        self.fields['completion_date'].label = 'Completion Date'
        self.fields['auditor'].label = 'Auditor'
        self.fields['description'].label = 'Description'
        self.fields['findings'].label = 'Findings'