from django.contrib import admin
from .models import Department, Employee, LeaveType, LeaveRequest, PerformanceReview, TimeEntry

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at', 'updated_at']
    ordering = ['name']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'department', 'position', 'hire_date', 'is_active', 'created_at']
    list_filter = ['department', 'position', 'is_active', 'hire_date', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'position']
    ordering = ['first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'profile_picture', 'address')
        }),
        ('Employment Information', {
            'fields': ('department', 'position', 'hire_date', 'salary', 'is_active')
        }),
        ('System Information', {
            'fields': ('user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date', 'end_date', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Leave Information', {
            'fields': ('employee', 'leave_type', 'start_date', 'end_date', 'reason')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_date')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ['employee', 'reviewer', 'review_date', 'overall_rating', 'status', 'created_at']
    list_filter = ['status', 'overall_rating', 'review_date', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'reviewer__username']
    ordering = ['-review_date']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Review Information', {
            'fields': ('employee', 'reviewer', 'review_date', 'review_period_start', 'review_period_end')
        }),
        ('Performance Assessment', {
            'fields': ('overall_rating', 'strengths', 'areas_for_improvement', 'goals', 'comments')
        }),
        ('Status & Acknowledgment', {
            'fields': ('status', 'employee_acknowledgment', 'acknowledgment_date')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'start_time', 'end_time', 'hours_worked', 'activity_type', 'is_billable', 'status', 'created_at']
    list_filter = ['status', 'activity_type', 'is_billable', 'date', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'description', 'client_case']
    ordering = ['-date', '-start_time']
    readonly_fields = ['created_at', 'updated_at', 'billable_amount']
    fieldsets = (
        ('Time Information', {
            'fields': ('employee', 'date', 'start_time', 'end_time', 'hours_worked')
        }),
        ('Activity Details', {
            'fields': ('activity_type', 'description', 'client_case')
        }),
        ('Billing Information', {
            'fields': ('is_billable', 'billable_rate', 'billable_amount')
        }),
        ('Status & Approval', {
            'fields': ('status', 'submitted_by', 'approved_by', 'approved_at')
        }),
        ('Additional Information', {
            'fields': ('notes', 'tags')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'submitted_by', 'approved_by')
