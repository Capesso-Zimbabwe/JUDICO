from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Invoice, InvoiceItem, Payment, Expense, Account, 
    JournalEntry, JournalEntryLine, PettyCash, Report,
    Journal, AccountingPeriod, AccountBalance, FinancialStatement,
    ExpenseCategory, ExpenseLineItem, AccountsPayable, AccountsPayableLineItem
)

# Register your models here.

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'journal_type', 'status', 'next_number', 'created_at']
    list_filter = ['journal_type', 'status']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'journal_type', 'description')
        }),
        ('Status', {
            'fields': ('status', 'next_number')
        }),
    )

@admin.register(AccountingPeriod)
class AccountingPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'status', 'is_current', 'is_adjustment_period', 'created_at']
    list_filter = ['status', 'is_current', 'is_adjustment_period']
    search_fields = ['name']
    ordering = ['-start_date']
    
    fieldsets = (
        ('Period Information', {
            'fields': ('name', 'start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status', 'is_current', 'is_adjustment_period')
        }),
        ('Balances', {
            'fields': ('opening_equity', 'closing_equity'),
            'classes': ('collapse',)
        }),
        ('Closing Information', {
            'fields': ('closed_by', 'closed_at', 'closing_notes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['closed_at', 'closing_equity']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('closed_by')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'account_category', 'normal_balance', 'current_balance_formatted', 'status']
    list_filter = ['account_type', 'account_category', 'status', 'normal_balance']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'account_type', 'account_category', 'parent_account', 'description')
        }),
        ('Balance Information', {
            'fields': ('opening_balance', 'current_balance', 'closing_balance', 'normal_balance')
        }),
        ('Account Properties', {
            'fields': ('is_bank_account', 'is_cash_account', 'is_contra_account')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )
    
    readonly_fields = ['current_balance', 'closing_balance']
    
    def current_balance_formatted(self, obj):
        return obj.formatted_balance
    current_balance_formatted.short_description = 'Current Balance'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent_account')

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_number', 'journal', 'date', 'description', 'period', 'status', 'total_debit', 'total_credit', 'is_balanced', 'created_by']
    list_filter = ['journal', 'period', 'status', 'date']
    search_fields = ['entry_number', 'description', 'reference']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Entry Information', {
            'fields': ('journal', 'entry_number', 'date', 'description', 'reference', 'period')
        }),
        ('Status', {
            'fields': ('status', 'total_debit', 'total_credit')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'posted_by', 'posted_at', 'reversed_by', 'reversed_at', 'reversal_reason'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['total_debit', 'total_credit', 'posted_at', 'reversed_at']
    
    def is_balanced(self, obj):
        return obj.is_balanced()
    is_balanced.boolean = True
    is_balanced.short_description = 'Balanced'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('journal', 'period', 'created_by', 'posted_by', 'reversed_by')

@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = ['journal_entry', 'account', 'description', 'debit', 'credit', 'side', 'is_adjustment', 'is_closing']
    list_filter = ['is_adjustment', 'is_closing', 'account__account_type']
    search_fields = ['journal_entry__entry_number', 'account__code', 'account__name', 'description']
    ordering = ['journal_entry__date', 'id']
    
    fieldsets = (
        ('Line Information', {
            'fields': ('journal_entry', 'account', 'description')
        }),
        ('Amounts', {
            'fields': ('debit', 'credit')
        }),
        ('Properties', {
            'fields': ('is_adjustment', 'is_closing')
        }),
    )
    
    def side(self, obj):
        return obj.side
    side.short_description = 'Side'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('journal_entry', 'account')

@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = ['account', 'period', 'opening_balance', 'period_debits', 'period_credits', 'closing_balance', 'net_movement']
    list_filter = ['period', 'account__account_type']
    search_fields = ['account__code', 'account__name', 'period__name']
    ordering = ['period__start_date', 'account__code']
    
    fieldsets = (
        ('Account and Period', {
            'fields': ('account', 'period')
        }),
        ('Balances', {
            'fields': ('opening_balance', 'period_debits', 'period_credits', 'closing_balance')
        }),
    )
    
    readonly_fields = ['closing_balance', 'net_movement']
    
    def net_movement(self, obj):
        return obj.net_movement
    net_movement.short_description = 'Net Movement'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account', 'period')

@admin.register(FinancialStatement)
class FinancialStatementAdmin(admin.ModelAdmin):
    list_display = ['statement_type', 'period', 'as_of_date', 'format', 'generated_by', 'generated_at']
    list_filter = ['statement_type', 'format', 'generated_at']
    search_fields = ['statement_type', 'period__name']
    readonly_fields = ['generated_at']
    date_hierarchy = 'generated_at'


# Expense Management Admin
@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'is_active', 'created_at']
    list_filter = ['is_active', 'account__account_category', 'created_at']
    search_fields = ['name', 'description', 'account__name']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'title', 'expense_category', 'total_amount', 
        'status', 'expense_date', 'vendor', 'created_by'
    ]
    list_filter = [
        'status', 'expense_type', 'expense_category', 'expense_date', 
        'created_at', 'period'
    ]
    search_fields = [
        'reference_number', 'title', 'description', 'vendor', 
        'expense_category__name'
    ]
    readonly_fields = [
        'reference_number', 'net_amount', 'created_at', 'updated_at',
        'journal_entry'
    ]
    date_hierarchy = 'expense_date'
    ordering = ['-expense_date', '-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'expense_type', 'status')
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'tax_amount', 'net_amount')
        }),
        ('Dates & Vendor', {
            'fields': ('expense_date', 'due_date', 'paid_date', 'vendor')
        }),
        ('Categorization', {
            'fields': ('expense_category', 'period')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_reference')
        }),
        ('System', {
            'fields': ('reference_number', 'journal_entry', 'created_by', 'approved_by', 'paid_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExpenseLineItem)
class ExpenseLineItemAdmin(admin.ModelAdmin):
    list_display = ['expense', 'description', 'quantity', 'unit_price', 'amount', 'tax_rate']
    list_filter = ['expense__expense_category', 'created_at']
    search_fields = ['description', 'expense__title', 'expense__reference_number']
    readonly_fields = ['amount', 'tax_amount', 'created_at', 'updated_at']
    ordering = ['expense', 'created_at']

@admin.register(AccountsPayable)
class AccountsPayableAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'vendor', 'vendor_invoice_number', 'invoice_date', 
        'due_date', 'total_amount', 'amount_paid', 'balance_due', 'status'
    ]
    list_filter = [
        'status', 'payment_terms', 'expense_category', 'period', 
        'is_recurring', 'created_at', 'invoice_date'
    ]
    search_fields = [
        'reference_number', 'vendor', 'vendor_invoice_number', 'description'
    ]
    readonly_fields = [
        'reference_number', 'balance_due', 'created_by', 'created_at', 
        'updated_at', 'approved_by', 'approved_at', 'paid_by', 'paid_date'
    ]
    date_hierarchy = 'invoice_date'
    ordering = ['-invoice_date', '-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'reference_number', 'vendor', 'vendor_invoice_number', 
                'invoice_date', 'due_date', 'payment_terms'
            )
        }),
        ('Amounts', {
            'fields': (
                'subtotal', 'tax_amount', 'total_amount', 'amount_paid', 'balance_due'
            )
        }),
        ('Status & Workflow', {
            'fields': (
                'status', 'is_recurring', 'recurring_frequency'
            )
        }),
        ('Accounting', {
            'fields': (
                'expense_category', 'period', 'journal_entry'
            )
        }),
        ('Additional Information', {
            'fields': (
                'description', 'notes', 'attachments'
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_by', 'created_at', 'updated_at', 'approved_by', 
                'approved_at', 'paid_by', 'paid_date', 'payment_method', 
                'payment_reference'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(AccountsPayableLineItem)
class AccountsPayableLineItemAdmin(admin.ModelAdmin):
    list_display = [
        'payable', 'description', 'quantity', 'unit_price', 'tax_rate', 'line_total'
    ]
    list_filter = ['expense_account', 'created_at']
    search_fields = ['description', 'payable__vendor']
    readonly_fields = ['line_total', 'created_at', 'updated_at']
    ordering = ['payable', 'id']
