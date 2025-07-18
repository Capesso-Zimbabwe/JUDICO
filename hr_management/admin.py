from django.contrib import admin
from .models import Department, Employee, LeaveType, LeaveRequest, PerformanceReview

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'department', 'position', 'is_active')
    list_filter = ('is_active', 'department', 'hire_date')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days_allowed', 'requires_approval')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reviewer', 'review_date', 'overall_rating', 'employee_acknowledgment')
    list_filter = ('overall_rating', 'employee_acknowledgment', 'review_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'reviewer__username')
