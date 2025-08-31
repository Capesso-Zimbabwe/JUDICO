from django import forms
from .models import Task
from django.contrib.auth.models import User
from lawyer_portal.models import LawyerProfile
from client_management.models import Client

class TaskFilterForm(forms.Form):
    search = forms.CharField(widget=forms.TextInput(
        attrs={
            'type': 'search',
            'placeholder': 'Search tasks...',
            'onchange': 'document.getElementById("search-form").submit();',
        }), required=False)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'client', 'assigned_to', 'status', 'priority', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs'}),
            'description': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs', 'rows': 4}),
            'client': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs'}),
            'assigned_to': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs'}),
            'status': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs'}),
            'priority': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs'}),
            'due_date': forms.DateInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-xs', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all active clients from the database
        clients = Client.objects.filter(is_active=True).order_by('name')
        self.fields['client'].queryset = clients
        # Explicitly set choices for client field
        self.fields['client'].choices = [('', '----------')] + [(client.id, client.name) for client in clients]
        
        # Filter assigned_to to only show lawyers
        lawyer_users = User.objects.filter(lawyer_profile__isnull=False).order_by('first_name', 'last_name', 'username')
        self.fields['assigned_to'].queryset = lawyer_users
        # Explicitly set choices for assigned_to field
        self.fields['assigned_to'].choices = [('', '----------')] + [(user.id, user.get_full_name() or user.username) for user in lawyer_users]
        
        # Ensure status and priority choices are properly set
        self.fields['status'].choices = [('', '----------')] + list(Task.STATUS_CHOICES)
        self.fields['priority'].choices = [('', '----------')] + list(Task.PRIORITY_CHOICES)