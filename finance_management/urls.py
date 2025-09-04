from django.urls import path
from . import views

app_name = 'finance_management'

urlpatterns = [
    # Dashboard
    path('', views.FinanceDashboardView.as_view(), name='dashboard'),
    
    # Chart of Accounts
    path('chart-of-accounts/', views.ChartOfAccountsView.as_view(), name='chart_of_accounts'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/update/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    
    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    

    
    # Income
    path('income/', views.IncomeListView.as_view(), name='income_list'),
    
    # Accounts
    path('accounts/create/', views.AccountCreateView.as_view(), name='account_create'),
    path('accounts/<str:code>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<str:code>/update/', views.AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<str:code>/transactions/', views.AccountTransactionsView.as_view(), name='account_transactions'),
    path('accounts/<str:code>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),
    path('api/accounts/<str:code>/', views.AccountDetailAPIView.as_view(), name='account_detail_api'),
    path('api/accounts/<str:code>/transactions/', views.AccountTransactionsAPIView.as_view(), name='account_transactions_api'),
    
    # Journal Entry URLs
    path('journal-entries/', views.JournalEntryListView.as_view(), name='journal_entries'),
    path('journal-entries/new/', views.JournalEntryCreateView.as_view(), name='journal_entry_create'),
    path('journal-entries/<int:pk>/', views.JournalEntryDetailView.as_view(), name='journal_entry_detail'),
    path('journal-entries/<int:pk>/update/', views.JournalEntryUpdateView.as_view(), name='journal_entry_update'),
    path('api/journal-entries/<int:pk>/', views.JournalEntryDetailAPIView.as_view(), name='journal_entry_detail_api'),
    path('api/journal-entries/<int:pk>/delete/', views.JournalEntryDeleteView.as_view(), name='journal_entry_delete'),
    
    # Petty Cash URLs
    path('petty-cash/', views.PettyCashListView.as_view(), name='petty_cash_list'),
    path('petty-cash/new/', views.PettyCashCreateView.as_view(), name='petty_cash_create'),
    path('petty-cash/<int:pk>/', views.PettyCashDetailView.as_view(), name='petty_cash_detail'),
    path('petty-cash/<int:pk>/update/', views.PettyCashUpdateView.as_view(), name='petty_cash_update'),
    path('api/petty-cash/<int:pk>/', views.PettyCashDetailAPIView.as_view(), name='petty_cash_detail_api'),
    path('api/petty-cash/<int:pk>/approve/', views.PettyCashApprovalView.as_view(), name='petty_cash_approve'),
    
    # Enhanced Accounting URLs
    
    # Journal Management
    path('journals/', views.JournalListView.as_view(), name='journal_list'),
    path('journals/create/', views.JournalCreateView.as_view(), name='journal_create'),
    path('journals/<int:pk>/update/', views.JournalUpdateView.as_view(), name='journal_update'),
    path('journals/<int:pk>/delete/', views.JournalDeleteView.as_view(), name='journal_delete'),
    
    # Accounting Periods
    path('periods/', views.AccountingPeriodListView.as_view(), name='period_list'),
    path('periods/create/', views.AccountingPeriodCreateView.as_view(), name='period_create'),
    path('periods/<int:pk>/', views.AccountingPeriodDetailView.as_view(), name='period_detail'),
    path('periods/<int:pk>/update/', views.AccountingPeriodUpdateView.as_view(), name='period_update'),
    path('periods/close/', views.PeriodClosingView.as_view(), name='period_closing'),
    
    # Enhanced Journal Entries
    path('journal-entries/', views.EnhancedJournalEntryListView.as_view(), name='enhanced_journal_entry_list'),
    path('journal-entries/create/', views.EnhancedJournalEntryCreateView.as_view(), name='enhanced_journal_entry_create'),
    path('journal-entries/<int:pk>/', views.EnhancedJournalEntryDetailView.as_view(), name='enhanced_journal_entry_detail'),
    path('journal-entries/<int:pk>/update/', views.EnhancedJournalEntryUpdateView.as_view(), name='enhanced_journal_entry_update'),
    path('journal-entries/<int:pk>/post/', views.JournalEntryPostView.as_view(), name='journal_entry_post'),
    path('journal-entries/<int:pk>/reverse/', views.JournalEntryReverseView.as_view(), name='journal_entry_reverse'),
    
    # Financial Reports
    path('reports/trial-balance/', views.TrialBalanceView.as_view(), name='trial_balance'),
    path('reports/balance-sheet/', views.BalanceSheetView.as_view(), name='balance_sheet'),
    path('reports/income-statement/', views.IncomeStatementView.as_view(), name='income_statement'),
    
    # Reports URLs
    path('reports/', views.ReportListView.as_view(), name='reports'),
    path('reports/new/', views.ReportCreateView.as_view(), name='report_create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/preview/', views.ReportPreviewView.as_view(), name='report_preview'),
    path('api/reports/<int:pk>/', views.ReportDetailAPIView.as_view(), name='report_detail_api'),
    path('api/reports/<int:pk>/download/', views.ReportDownloadView.as_view(), name='report_download'),
    path('api/reports/<int:pk>/delete/', views.ReportDeleteView.as_view(), name='report_delete'),

    # Expense Management
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('expenses/<int:pk>/update/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    path('expenses/<int:pk>/approve/', views.ExpenseApprovalView.as_view(), name='expense_approve'),
    path('expenses/<int:pk>/pay/', views.ExpensePaymentView.as_view(), name='expense_pay'),
    path('expenses/dashboard/', views.ExpenseDashboardView.as_view(), name='expense_dashboard'),
    
    # Expense Categories
    path('expense-categories/', views.ExpenseCategoryListView.as_view(), name='expense_category_list'),
    path('expense-categories/create/', views.ExpenseCategoryCreateView.as_view(), name='expense_category_create'),
    path('expense-categories/<int:pk>/update/', views.ExpenseCategoryUpdateView.as_view(), name='expense_category_update'),
    path('expense-categories/<int:pk>/delete/', views.ExpenseCategoryDeleteView.as_view(), name='expense_category_delete'),

    # Accounts Payable URLs
    path('accounts-payable/', views.AccountsPayableListView.as_view(), name='accounts_payable_list'),
    path('accounts-payable/create/', views.AccountsPayableCreateView.as_view(), name='accounts_payable_create'),
    path('accounts-payable/<int:pk>/', views.AccountsPayableDetailView.as_view(), name='accounts_payable_detail'),
    path('accounts-payable/<int:pk>/edit/', views.AccountsPayableUpdateView.as_view(), name='accounts_payable_update'),
    path('accounts-payable/<int:pk>/delete/', views.AccountsPayableDeleteView.as_view(), name='accounts_payable_delete'),
    path('accounts-payable/<int:pk>/approve/', views.AccountsPayableApprovalView.as_view(), name='accounts_payable_approve'),
    path('accounts-payable/<int:pk>/payment/', views.AccountsPayablePaymentView.as_view(), name='accounts_payable_payment'),
    
    # Accounts Receivable URLs
    path('accounts-receivable/', views.AccountsReceivableListView.as_view(), name='accounts_receivable_list'),
    path('accounts-receivable/<int:pk>/', views.AccountsReceivableDetailView.as_view(), name='accounts_receivable_detail'),
    path('accounts-receivable/<int:pk>/payment/', views.AccountsReceivablePaymentView.as_view(), name='accounts_receivable_payment'),
]