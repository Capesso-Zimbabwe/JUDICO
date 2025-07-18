from django import forms
from .models import Employee, LeaveRequest, PerformanceReview, Department, LeaveType
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class EmployeeForm(forms.ModelForm):
    USER_TYPE_CHOICES = [
        ('', 'Select User Type (Optional)'),
        ('lawyer', 'Lawyer'),
    ]
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        required=False,
        label="Register as Lawyer",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Employee
        fields = ['user', 'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 
                 'profile_picture', 'address', 'department', 'position', 
                 'hire_date', 'salary', 'is_active']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = ['employee', 'reviewer', 'review_date', 'review_period_start', 
                 'review_period_end', 'overall_rating', 'strengths', 
                 'areas_for_improvement', 'goals', 'comments']
        widgets = {
            'review_date': forms.DateInput(attrs={'type': 'date'}),
            'review_period_start': forms.DateInput(attrs={'type': 'date'}),
            'review_period_end': forms.DateInput(attrs={'type': 'date'}),
            'strengths': forms.Textarea(attrs={'rows': 3}),
            'areas_for_improvement': forms.Textarea(attrs={'rows': 3}),
            'goals': forms.Textarea(attrs={'rows': 3}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }

class UserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('', 'Select User Type'),
        ('client', 'Client'),
        ('lawyer', 'Lawyer'),
    ]
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter email address'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter last name'
        })
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        required=True,
        label="User Type",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add styling to inherited fields
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Confirm password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean_user_type(self):
        user_type = self.cleaned_data.get('user_type')
        if not user_type:
            raise forms.ValidationError("Please select a user type.")
        return user_type
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')