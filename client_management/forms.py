from django import forms
from django.contrib.auth.models import User

from client_management.models import Client, ClientDocument, Case, CaseUpdate, CaseDocument
from lawyer_portal.models import LawyerProfile


class ClientForm(forms.ModelForm):

    class Meta:
        model = Client
        fields = [
            'name',
            'contact_person',
            'email',
            'phone',
            'address',
            'is_active',
            'assigned_lawyer',
            'case_type',
            # 'registration_date',
        ]

        widgets = {
            "address": forms.Textarea(attrs={'rows': 2, 'cols': 20}),
        }


class ClientFilterForm(forms.Form):
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search clients...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)

class ClientDocumentForm(forms.ModelForm):
    class Meta:
        model = ClientDocument
        fields = ['title', 'document']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Document Title'}),
            'document': forms.ClearableFileInput(attrs={'multiple': False}),
        }

class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            'client',
            'title',
            'description',
            'case_type',
            'status',
            'priority',
            'assigned_lawyer',
            'lawyer',
            'start_date',
            'expected_completion_date',
            'court_date',
            'court_location',
            'case_value',
            'is_billable',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_completion_date': forms.DateInput(attrs={'type': 'date'}),
            'court_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'court_location': forms.TextInput(attrs={'placeholder': 'Court Location'}),
            'case_value': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
        }

class CaseFilterForm(forms.Form):
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search cases...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Case.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Case.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )
    
    case_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Client.CASE_TYPES,
        required=False,
        widget=forms.Select(attrs={'onchange': 'document.getElementById("search-form").submit();'})
    )

class CaseUpdateForm(forms.ModelForm):
    class Meta:
        model = CaseUpdate
        fields = [
            'title',
            'description',
            'update_type',
            'hours_spent',
            'is_billable',
            'next_action',
            'next_action_date',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
            'next_action': forms.Textarea(attrs={'rows': 3, 'cols': 50}),
            'next_action_date': forms.DateInput(attrs={'type': 'date'}),
            'hours_spent': forms.NumberInput(attrs={'step': '0.25', 'placeholder': '0.00'}),
        }

class CaseDocumentForm(forms.ModelForm):
    class Meta:
        model = CaseDocument
        fields = ['title', 'document', 'document_type']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Document Title'}),
            'document': forms.ClearableFileInput(attrs={'multiple': False}),
        }