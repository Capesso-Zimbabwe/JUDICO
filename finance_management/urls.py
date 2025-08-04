from django.urls import path
from . import views

app_name = 'finance_management'

urlpatterns = [
    path('', views.FinanceDashboardView.as_view(), name='dashboard'),
    path('chart-of-accounts/', views.ChartOfAccountsView.as_view(), name='chart_of_accounts'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('expenses/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/approve/', views.ExpenseApprovalView.as_view(), name='expense_approve'),
    path('api/expenses/<int:pk>/', views.ExpenseDetailAPIView.as_view(), name='expense_detail_api'),
    path('accounts/create/', views.AccountCreateView.as_view(), name='account_create'),
    path('accounts/<str:code>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<str:code>/update/', views.AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<str:code>/transactions/', views.AccountTransactionsView.as_view(), name='account_transactions'),
    path('api/accounts/<str:code>/', views.AccountDetailAPIView.as_view(), name='account_detail_api'),
    # Journal Entry URLs
    path('journal-entries/', views.JournalEntryListView.as_view(), name='journal_entries'),
    path('journal-entries/create/', views.JournalEntryCreateView.as_view(), name='journal_entry_create'),
    path('journal-entries/<int:pk>/', views.JournalEntryDetailView.as_view(), name='journal_entry_detail'),
    path('journal-entries/<int:pk>/update/', views.JournalEntryUpdateView.as_view(), name='journal_entry_update'),
    path('api/journal-entries/<int:pk>/', views.JournalEntryDetailAPIView.as_view(), name='journal_entry_detail_api'),
]