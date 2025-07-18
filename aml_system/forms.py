from django import forms
from django.contrib.auth.models import User
from .models import Screening, Entity, Alert, ScreeningResult

class EntityForm(forms.ModelForm):
    """Form for creating and editing entities"""
    
    class Meta:
        model = Entity
        fields = ['name', 'entity_type', 'date_of_birth', 'place_of_birth', 
                 'nationality', 'identification_number', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter entity name'
            }),
            'entity_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'place_of_birth': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter place of birth'
            }),
            'nationality': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter nationality'
            }),
            'identification_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter ID number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
        }
        labels = {
            'name': 'Entity Name*',
            'entity_type': 'Entity Type*',
            'date_of_birth': 'Date of Birth',
            'place_of_birth': 'Place of Birth',
            'nationality': 'Nationality',
            'identification_number': 'Identification Number',
            'address': 'Address',
        }

class ScreeningForm(forms.ModelForm):
    """Form for creating and editing screenings"""
    
    entity = forms.ModelChoiceField(
        queryset=Entity.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        empty_label="Select an entity"
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        empty_label="Assign to user (optional)"
    )
    
    class Meta:
        model = Screening
        fields = ['entity', 'screening_type', 'status', 'risk_level', 'assigned_to', 'notes']
        widgets = {
            'screening_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'risk_level': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Enter any additional notes or comments'
            }),
        }
        labels = {
            'entity': 'Entity to Screen*',
            'screening_type': 'Screening Type*',
            'status': 'Status',
            'risk_level': 'Risk Level',
            'assigned_to': 'Assigned To',
            'notes': 'Notes',
        }

class ScreeningFilterForm(forms.Form):
    """Form for filtering screenings"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'border rounded-lg px-4 py-2 w-64',
            'placeholder': 'Search screenings...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('all', 'All Status')] + Screening.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'border rounded-lg px-4 py-2'
        })
    )
    
    risk_level = forms.ChoiceField(
        choices=[('all', 'All Risk Levels')] + Screening.RISK_LEVELS,
        required=False,
        widget=forms.Select(attrs={
            'class': 'border rounded-lg px-4 py-2'
        })
    )

class AlertForm(forms.ModelForm):
    """Form for creating and editing alerts"""
    
    class Meta:
        model = Alert
        fields = ['alert_type', 'priority', 'status', 'entity', 'title', 'description', 'assigned_to']
        widgets = {
            'alert_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'entity': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter alert title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Enter alert description'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

class ScreeningResultForm(forms.ModelForm):
    """Form for reviewing screening results"""
    
    class Meta:
        model = ScreeningResult
        fields = ['is_false_positive', 'review_notes']
        widgets = {
            'is_false_positive': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'review_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Enter review notes'
            }),
        }
        labels = {
            'is_false_positive': 'Mark as False Positive',
            'review_notes': 'Review Notes',
        }