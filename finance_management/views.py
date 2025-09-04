from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.db.models import Q, Sum, Count
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from decimal import Decimal
import json
from .models import (
    Invoice, InvoiceItem, Payment, Expense, Account, 
    JournalEntry, JournalEntryLine, PettyCash, Report,
    Journal, AccountingPeriod, AccountBalance, FinancialStatement,
    ExpenseCategory, AccountsPayable, AccountsPayableLineItem
)
from .forms import (
    InvoiceForm, PaymentForm, ExpenseForm, ExpenseFilterForm, 
    AccountForm, AccountFilterForm, JournalEntryForm, JournalEntryFilterForm, 
    JournalEntryLineFormSet, InvoiceFilterForm, PettyCashForm, 
    PettyCashFilterForm, ReportForm, ReportFilterForm,
    JournalForm, AccountingPeriodForm, FinancialStatementForm, PeriodClosingForm,
    ExpenseApprovalForm, ExpensePaymentForm, ExpenseLineItemFormSet,
    ExpenseCategoryForm, AccountsPayableForm, AccountsPayableLineItemFormSet,
    AccountsPayableApprovalForm, AccountsPayablePaymentForm, AccountsPayableFilterForm
)
from client_management.models import Client

class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate real financial metrics
        # Cash Position (Total payments received - Total expenses paid)
        total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_expenses_paid = Expense.objects.filter(status='APPROVED').aggregate(total=Sum('total_amount'))['total'] or 0
        cash_position = total_payments - total_expenses_paid
        
        # Accounts Receivable (Unpaid invoices)
        accounts_receivable = Invoice.objects.filter(status__in=['SENT', 'OVERDUE']).aggregate(total=Sum('total'))['total'] or 0
        
        # Accounts Payable (Unpaid accounts payable)
        accounts_payable = AccountsPayable.objects.filter(status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PARTIALLY_PAID']).aggregate(total=Sum('balance_due'))['total'] or 0
        
        # Working Capital (Current Assets - Current Liabilities)
        working_capital = cash_position + accounts_receivable - accounts_payable
        
        # Set dashboard metrics
        context['cash_position'] = cash_position
        context['accounts_receivable'] = accounts_receivable
        context['accounts_payable'] = accounts_payable
        context['working_capital'] = working_capital
        
        # Get invoice counts by status
        context['paid_count'] = Invoice.objects.filter(status='PAID').count()
        context['overdue_count'] = Invoice.objects.filter(status='OVERDUE').count()
        context['sent_count'] = Invoice.objects.filter(status='SENT').count()
        context['draft_count'] = Invoice.objects.filter(status='DRAFT').count()
        
        # Get recent payments
        context['recent_payments'] = Payment.objects.select_related('invoice__client').order_by('-payment_date')[:5]
        
        # Get recent expenses
        context['recent_expenses'] = Expense.objects.order_by('-expense_date')[:5]
        
        # Get recent accounts payable
        context['recent_payables'] = AccountsPayable.objects.order_by('-invoice_date')[:5]
        
        # Calculate monthly revenue and expenses for the current year
        current_year = timezone.now().year
        monthly_revenue = [0] * 12
        monthly_expenses = [0] * 12
        monthly_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Get monthly revenue from payments
        payments = Payment.objects.filter(payment_date__year=current_year)
        for payment in payments:
            month_index = payment.payment_date.month - 1  # 0-based index
            monthly_revenue[month_index] += float(payment.amount)
        
        # Get monthly expenses
        expenses = Expense.objects.filter(expense_date__year=current_year)
        for expense in expenses:
            month_index = expense.expense_date.month - 1  # 0-based index
            monthly_expenses[month_index] += float(expense.total_amount)
        
        # Get expense categories distribution
        expense_categories_data = []
        expense_categories_labels = []
        
        # Get all expense categories that have expenses
        categories_with_expenses = Expense.objects.values('expense_category__name').annotate(
            total=Sum('total_amount')
        ).filter(expense_category__isnull=False).order_by('-total')
        
        for category in categories_with_expenses:
            if category['total'] > 0:
                expense_categories_data.append(float(category['total']))
                expense_categories_labels.append(category['expense_category__name'] or 'Unknown')
        
        # Invoice status distribution
        invoice_status_data = [
            context['paid_count'],
            context['sent_count'],
            context['overdue_count'],
            context['draft_count']
        ]
        
        # Top clients by revenue
        top_clients = Payment.objects.select_related('invoice__client').values('invoice__client__name').annotate(
            total_revenue=Sum('amount')
        ).order_by('-total_revenue')[:5]
        
        client_revenue_labels = []
        client_revenue_data = []
        for client in top_clients:
            client_revenue_labels.append(client['invoice__client__name'] or 'Unknown Client')
            client_revenue_data.append(float(client['total_revenue']))
        
        # Calculate real financial metrics
        # Collection Rate (Paid invoices / Total invoices)
        total_invoices = Invoice.objects.count()
        paid_invoices = Invoice.objects.filter(status='PAID').count()
        collection_rate = (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
        
        # Average Payment Time (in days)
        paid_payments = Payment.objects.filter(payment_date__isnull=False)
        if paid_payments.exists():
            total_days = 0
            payment_count = 0
            for payment in paid_payments:
                if payment.invoice and payment.invoice.issue_date:
                    days_diff = (payment.payment_date - payment.invoice.issue_date).days
                    if days_diff >= 0:  # Only count valid payment times
                        total_days += days_diff
                        payment_count += 1
            
            avg_payment_time = total_days / payment_count if payment_count > 0 else 0
        else:
            avg_payment_time = 0
        
        # Outstanding Amount (Unpaid invoices)
        outstanding_amount = Invoice.objects.filter(status__in=['SENT', 'OVERDUE']).aggregate(total=Sum('total'))['total'] or 0
        
        # Monthly Growth (Compare current month vs previous month)
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        # Current month revenue
        current_month_revenue = Payment.objects.filter(
            payment_date__year=current_year,
            payment_date__month=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Previous month revenue
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year
            
        prev_month_revenue = Payment.objects.filter(
            payment_date__year=prev_year,
            payment_date__month=prev_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate growth percentage
        if prev_month_revenue > 0:
            growth_percentage = ((current_month_revenue - prev_month_revenue) / prev_month_revenue) * 100
            monthly_growth = f"{growth_percentage:+.1f}"
        else:
            monthly_growth = "+0.0"
        
        # Finance Status
        overdue_invoices = Invoice.objects.filter(status='OVERDUE').count()
        pending_expenses = Expense.objects.filter(status='PENDING').count()
        pending_payables = AccountsPayable.objects.filter(status__in=['DRAFT', 'PENDING_APPROVAL']).count()
        
        if overdue_invoices > 0 and (pending_expenses > 0 or pending_payables > 0):
            finance_status = f"{overdue_invoices} overdue invoices, {pending_expenses} pending expenses, {pending_payables} pending payables"
        elif overdue_invoices > 0:
            finance_status = f"{overdue_invoices} overdue invoices need attention"
        elif pending_expenses > 0 or pending_payables > 0:
            finance_status = f"{pending_expenses} pending expenses, {pending_payables} pending payables require approval"
        else:
            finance_status = "All financial reports up to date"
        
        # Set calculated metrics
        context['collection_rate'] = round(collection_rate, 1)
        context['avg_payment_time'] = round(avg_payment_time, 0)
        context['outstanding_amount'] = outstanding_amount
        context['monthly_growth'] = monthly_growth
        context['finance_status'] = finance_status
        
        # Payment Methods Distribution
        payment_methods_data = []
        payment_methods_labels = ['Bank Transfer', 'Credit Card', 'Cash', 'Check', 'Online']
        
        # Count payments by method
        bank_transfer_count = Payment.objects.filter(payment_method='BANK_TRANSFER').count()
        credit_card_count = Payment.objects.filter(payment_method='CREDIT_CARD').count()
        cash_count = Payment.objects.filter(payment_method='CASH').count()
        check_count = Payment.objects.filter(payment_method='CHECK').count()
        online_count = Payment.objects.filter(payment_method='ONLINE_PAYMENT').count()
        
        payment_methods_data = [bank_transfer_count, credit_card_count, cash_count, check_count, online_count]
        
        # Cash Flow Trends (Last 6 months)
        cash_flow_data = []
        cash_flow_labels = []
        
        for i in range(6):
            month_offset = 5 - i  # Start from 5 months ago
            target_date = timezone.now() - timedelta(days=30 * month_offset)
            target_month = target_date.month
            target_year = target_date.year
            
            # Calculate net cash flow for this month
            month_payments = Payment.objects.filter(
                payment_date__year=target_year,
                payment_date__month=target_month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            month_expenses = Expense.objects.filter(
                expense_date__year=target_year,
                expense_date__month=target_month
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            net_cash_flow = month_payments - month_expenses
            cash_flow_data.append(net_cash_flow)
            cash_flow_labels.append(target_date.strftime('%b'))
        
        # Convert data to JSON for charts (convert Decimal to float for JSON serialization)
        context['monthly_revenue'] = json.dumps([float(x) for x in monthly_revenue])
        context['monthly_expenses'] = json.dumps([float(x) for x in monthly_expenses])
        context['monthly_labels'] = json.dumps(monthly_labels)
        context['expense_categories_data'] = json.dumps([float(x) for x in expense_categories_data])
        context['expense_categories_labels'] = json.dumps(expense_categories_labels)
        context['invoice_status_data'] = json.dumps(invoice_status_data)
        context['client_revenue_labels'] = json.dumps(client_revenue_labels)
        context['client_revenue_data'] = json.dumps([float(x) for x in client_revenue_data])
        context['payment_methods_data'] = json.dumps(payment_methods_data)
        context['payment_methods_labels'] = json.dumps(payment_methods_labels)
        context['cash_flow_data'] = json.dumps([float(x) for x in cash_flow_data])
        context['cash_flow_labels'] = json.dumps(cash_flow_labels)
        
        return context

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'finance_management/invoice_list.html'
    context_object_name = 'invoices'
    ordering = ['-issue_date']
    paginate_by = 10  # Show 10 invoices per page
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_param = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        
        if search_param:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_param) |
                Q(client__name__icontains=search_param) |
                Q(status__icontains=search_param)
            )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize search form
        search_param = self.request.GET.get('search')
        initial = {}
        if search_param:
            initial['search'] = search_param
        search_form = InvoiceFilterForm(initial=initial)
        
        context['search_form'] = search_form
        return context

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'finance_management/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        return context

class InvoiceCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = InvoiceForm()
        clients = Client.objects.all()
        return render(request, 'finance_management/modals/new_invoice_modal.html', {
            'form': form, 
            'clients': clients,
            'modal_id': 'new-invoice-modal'
        })
    
    def post(self, request):
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            messages.success(request, 'Invoice created successfully.')
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:income_list')
            return response
        clients = Client.objects.all()
        return render(request, 'finance_management/modals/new_invoice_modal.html', {
            'form': form, 
            'clients': clients,
            'modal_id': 'new-invoice-modal'
        })

class InvoiceUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        form = InvoiceForm(instance=invoice)
        clients = Client.objects.all()
        return render(request, 'finance_management/modals/new_invoice_modal.html', {
            'form': form, 
            'clients': clients,
            'modal_id': 'edit-invoice-modal',
            'invoice': invoice
        })
    
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice updated successfully.')
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:income_list')
            return response
        clients = Client.objects.all()
        return render(request, 'finance_management/modals/new_invoice_modal.html', {
            'form': form, 
            'clients': clients,
            'modal_id': 'edit-invoice-modal',
            'invoice': invoice
        })

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'finance_management/payment_list.html'
    context_object_name = 'payments'
    ordering = ['-payment_date']

class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance_management/payment_form.html'
    success_url = reverse_lazy('payment_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment recorded successfully.')
        return super().form_valid(form)

class ExpenseListView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/expense_list.html'
    
    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
        
        context = super().get_context_data(**kwargs)
        
        # Get expenses from the database
        expenses = Expense.objects.all().order_by('-expense_date')
        
        # Handle search functionality
        search_param = self.request.GET.get('search')
        if search_param:
            expenses = expenses.filter(
                Q(title__icontains=search_param) |
                Q(description__icontains=search_param) |
                Q(category__icontains=search_param)
            )
        
        # Pagination
        paginator = Paginator(expenses, 10)  # Show 10 expenses per page
        page = self.request.GET.get('page')
        
        try:
            expenses = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            expenses = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            expenses = paginator.page(paginator.num_pages)
        
        # Initialize search form
        initial = {}
        if search_param:
            initial['search'] = search_param
        search_form = ExpenseFilterForm(initial=initial)
        
        # Add form for the modal
        expense_form = ExpenseForm()
        
        context['expenses'] = expenses
        context['page_obj'] = expenses  # For paginator component
        context['search_form'] = search_form
        context['form'] = expense_form
        
        return context

class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'finance_management/expense_detail.html'
    context_object_name = 'expense'

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance_management/expense_form.html'
    
    def get_success_url(self):
        return reverse_lazy('finance_management:expense_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        expense = form.save()
        messages.success(self.request, 'Expense recorded successfully.')
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse_lazy('finance_management:expense_list')
        return response
    
    def form_invalid(self, form):
        # Add debugging for form errors
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.cleaned_data if hasattr(form, 'cleaned_data') else 'No cleaned data'}")
        return super().form_invalid(form)

class ChartOfAccountsView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/chart_of_accounts.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get accounts from the database
        accounts = Account.objects.all().order_by('code')
        
        # Handle search functionality
        search_param = self.request.GET.get('search')
        type_filter = self.request.GET.get('filter')
        
        if search_param:
            accounts = accounts.filter(
                Q(name__icontains=search_param) |
                Q(code__icontains=search_param) |
                Q(account_type__icontains=search_param)
            )
        
        if type_filter:
            accounts = accounts.filter(account_type=type_filter)
        
        # Calculate actual balances from journal entries
        for account in accounts:
            # Calculate balance from journal entry lines
            debit_total = JournalEntryLine.objects.filter(
                account=account,
                journal_entry__status='POSTED'
            ).aggregate(total=Sum('debit'))['total'] or Decimal('0.00')
            
            credit_total = JournalEntryLine.objects.filter(
                account=account,
                journal_entry__status='POSTED'
            ).aggregate(total=Sum('credit'))['total'] or Decimal('0.00')
            
            # Calculate net balance from journal entries
            if account.account_type in ['ASSET', 'EXPENSE']:
                # Debit accounts: positive balance = debit > credit
                account.calculated_balance = debit_total - credit_total
            else:
                # Credit accounts: positive balance = credit > debit
                account.calculated_balance = credit_total - debit_total
            
            # Only update balance if there are journal entries
            if debit_total > 0 or credit_total > 0:
                account.balance = account.calculated_balance
                account.save()
        
        # Pagination
        paginator = Paginator(accounts, 20)  # Show 20 accounts per page
        page = self.request.GET.get('page')
        
        try:
            accounts_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            accounts_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            accounts_page = paginator.page(paginator.num_pages)
        
        # Initialize search form
        initial = {}
        if search_param:
            initial['search'] = search_param
        search_form = AccountFilterForm(initial=initial)
        
        context['accounts'] = accounts_page
        context['search_form'] = search_form
        context['paginator'] = paginator
        context['page_obj'] = accounts_page
        
        return context

class AccountCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = AccountForm()
        return render(request, 'finance_management/account_form.html', {'form': form})
    
    def post(self, request):
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save()
            messages.success(request, 'Account created successfully.')
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:chart_of_accounts')
            return response
        return render(request, 'finance_management/account_form.html', {'form': form})

class AccountDetailView(LoginRequiredMixin, DetailView):
    model = Account
    template_name = 'finance_management/account_detail.html'
    context_object_name = 'account'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data for account details
        return context

class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'finance_management/account_update.html'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    
    def get_success_url(self):
        return reverse_lazy('finance_management:chart_of_accounts')
    
    def form_valid(self, form):
        messages.success(self.request, 'Account updated successfully.')
        return super().form_valid(form)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Account updated successfully'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

class AccountTransactionsView(LoginRequiredMixin, DetailView):
    model = Account
    template_name = 'finance_management/account_transactions.html'
    context_object_name = 'account'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # For now, we'll use sample data since we don't have transaction models yet
        # In a real application, you would fetch actual transactions related to this account
        context['transactions'] = []
        context['total_debits'] = 0
        context['total_credits'] = 0
        context['net_balance'] = self.object.balance
        context['transaction_count'] = 0
        return context

class AccountDetailAPIView(LoginRequiredMixin, View):
    """API view to return account details as JSON for modal population"""
    
    def get(self, request, code):
        try:
            account = get_object_or_404(Account, code=code)
            data = {
                'code': account.code,
                'name': account.name,
                'type': account.get_account_type_display(),
                'balance': str(account.balance),
                'status': account.get_status_display(),
                'description': account.description,
                'created_date': account.created_at.strftime('%Y-%m-%d'),
            }
            return JsonResponse(data)
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)

class AccountTransactionsAPIView(LoginRequiredMixin, View):
    """API view to return account transactions as JSON"""
    
    def get(self, request, code):
        try:
            account = get_object_or_404(Account, code=code)
            transactions = JournalEntryLine.objects.filter(
                account=account,
                journal_entry__status='POSTED'
            ).select_related('journal_entry').order_by('journal_entry__date')

            data = []
            for transaction in transactions:
                data.append({
                    'date': transaction.journal_entry.date.strftime('%Y-%m-%d'),
                    'reference': transaction.journal_entry.entry_number,
                    'description': transaction.description or transaction.journal_entry.description,
                    'debit': str(transaction.debit),
                    'credit': str(transaction.credit),
                    'status': transaction.journal_entry.get_status_display(),
                })
            return JsonResponse(data, safe=False)
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)

class JournalEntryListView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/journal_entries.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get journal entries from the database
        journal_entries = JournalEntry.objects.all().order_by('-date', '-created_at')
        
        # Handle search and filter functionality
        search_param = self.request.GET.get('search')
        status_param = self.request.GET.get('status')
        
        if search_param:
            journal_entries = journal_entries.filter(
                Q(entry_number__icontains=search_param) |
                Q(description__icontains=search_param) |
                Q(reference__icontains=search_param)
            )
        
        if status_param:
            journal_entries = journal_entries.filter(status=status_param)
        
        # Pagination
        paginator = Paginator(journal_entries, 10)  # Show 10 journal entries per page
        page = self.request.GET.get('page')
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Initialize search form
        initial = {}
        if search_param:
            initial['search'] = search_param
        if status_param:
            initial['status'] = status_param
        search_form = JournalEntryFilterForm(initial=initial)
        
        context['journal_entries'] = page_obj
        context['page_obj'] = page_obj
        context['search_form'] = search_form
        context['accounts'] = Account.objects.filter(status='ACTIVE').order_by('code')
        
        return context

class JournalEntryCreateView(LoginRequiredMixin, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'finance_management/journal_entry_form.html'
    success_url = reverse_lazy('finance_management:journal_entries')
    
    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['finance_management/journal_entry_modal_form.html']
        return [self.template_name]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = JournalEntryLineFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = JournalEntryLineFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.created_by = self.request.user
            
            # Calculate totals from formset
            total_debit = 0
            total_credit = 0
            
            for line_form in formset:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE', False):
                    debit = line_form.cleaned_data.get('debit', 0) or 0
                    credit = line_form.cleaned_data.get('credit', 0) or 0
                    total_debit += debit
                    total_credit += credit
            
            journal_entry.total_debit = total_debit
            journal_entry.total_credit = total_credit
            journal_entry.save()
            
            formset.instance = journal_entry
            formset.save()
            
            if self.request.headers.get('HX-Request'):
                from django.contrib import messages
                from django.http import HttpResponse
                messages.success(self.request, "Journal entry created successfully.")
                response = HttpResponse(status=204)
                response["HX-Redirect"] = reverse_lazy('finance_management:journal_entries')
                return response
            else:
                messages.success(self.request, 'Journal entry created successfully.')
                return super().form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

class JournalEntryDetailView(LoginRequiredMixin, DetailView):
    model = JournalEntry
    template_name = 'finance_management/journal_entry_detail.html'
    context_object_name = 'journal_entry'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all()
        return context

class JournalEntryUpdateView(LoginRequiredMixin, UpdateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'finance_management/journal_entry_form.html'
    
    def get_success_url(self):
        return reverse_lazy('finance_management:journal_entries')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = JournalEntryLineFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = JournalEntryLineFormSet(instance=self.object)
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = JournalEntryLineFormSet(instance=self.object)
        
        # For HTMX requests, return only the modal content
        if request.headers.get('HX-Request'):
            return render(request, 'finance_management/modals/journal_entry_edit_modal.html', {
                'form': form,
                'formset': formset,
                'journal_entry': self.object,
                'modal_id': 'journal-edit-modal'
            })
        
        # For regular requests, return the full page
        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'journal_entry': self.object
        })
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            # Calculate totals from formset
            total_debit = 0
            total_credit = 0
            
            for line_form in formset:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE', False):
                    debit = line_form.cleaned_data.get('debit', 0) or 0
                    credit = line_form.cleaned_data.get('credit', 0) or 0
                    total_debit += debit
                    total_credit += credit
            
            form.instance.total_debit = total_debit
            form.instance.total_credit = total_credit
            
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, 'Journal entry updated successfully.')
            
            # For HTMX requests, return a redirect response
            if self.request.headers.get('HX-Request'):
                response = HttpResponse(status=204)
                response['HX-Redirect'] = reverse_lazy('finance_management:journal_entries')
                return response
            
            return super().form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        formset = JournalEntryLineFormSet(self.request.POST, instance=self.object)
        
        # For HTMX requests, return the modal content with form errors
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'finance_management/modals/journal_entry_edit_modal.html', {
                'form': form,
                'formset': formset,
                'journal_entry': self.object,
                'modal_id': 'journal-edit-modal'
            })
        
        # For regular requests, return the full page
        return render(self.request, self.template_name, {
            'form': form,
            'formset': formset,
            'journal_entry': self.object
        })

class JournalEntryDetailAPIView(LoginRequiredMixin, View):
    """API view to return journal entry details as JSON for modal population"""
    
    def get(self, request, pk):
        try:
            journal_entry = get_object_or_404(JournalEntry, pk=pk)
            lines_data = []
            for line in journal_entry.lines.all():
                lines_data.append({
                    'account_code': line.account.code,
                    'account_name': line.account.name,
                    'description': line.description,
                    'debit': str(line.debit),
                    'credit': str(line.credit),
                })
            
            data = {
                'entry_number': journal_entry.entry_number,
                'date': journal_entry.date.strftime('%Y-%m-%d'),
                'description': journal_entry.description,
                'reference': journal_entry.reference,
                'status': journal_entry.get_status_display(),
                'total_debit': str(journal_entry.total_debit),
                'total_credit': str(journal_entry.total_credit),
                'is_balanced': journal_entry.is_balanced(),
                'created_by': journal_entry.created_by.get_full_name() or journal_entry.created_by.username,
                'created_at': journal_entry.created_at.strftime('%Y-%m-%d %H:%M'),
                'lines': lines_data,
            }
            return JsonResponse(data)
        except JournalEntry.DoesNotExist:
            return JsonResponse({'error': 'Journal entry not found'}, status=404)

class JournalEntryDeleteView(LoginRequiredMixin, View):
    """View to handle journal entry deletion"""
    
    def post(self, request, pk):
        try:
            journal_entry = get_object_or_404(JournalEntry, pk=pk)
            entry_number = journal_entry.entry_number
            journal_entry.delete()
            
            messages.success(request, f'Journal Entry "{entry_number}" has been deleted successfully.')
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:journal_entries')
            return response
            
        except JournalEntry.DoesNotExist:
            return JsonResponse({'error': 'Journal entry not found'}, status=404)

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance_management/expense_form.html'
    
    def get_success_url(self):
        return reverse_lazy('finance_management:expense_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Expense updated successfully.')
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse_lazy('finance_management:expense_list')
        return response
    
    def form_invalid(self, form):
        # Handle form errors for HTMX requests
        if self.request.headers.get('HX-Request'):
            # Return the modal content with form errors
            return render(self.request, 'finance_management/update_expense_modal.html', {
                'form': form, 
                'expense': self.object,
                'modal_id': 'update-expense-modal'
            })
        
        # For regular requests, return the full page
        return super().form_invalid(form)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        # For HTMX requests (from JavaScript fetch with HX-Request header), return only the form content
        if request.headers.get('HX-Request'):
            return render(request, self.template_name, {'form': form, 'expense': self.object})
        
        # For regular page requests, return the complete modal structure
        return render(request, 'finance_management/update_expense_modal.html', {
            'form': form, 
            'expense': self.object,
            'modal_id': 'update-expense-modal'
        })

class ExpenseApprovalView(LoginRequiredMixin, View):
    """API view to approve an expense"""
    
    def post(self, request, pk):
        try:
            expense = get_object_or_404(Expense, pk=pk)
            expense.approved_by = request.user
            expense.save()
            
            messages.success(request, f'Expense "{expense.title}" has been approved.')
            return JsonResponse({'success': True, 'message': 'Expense approved successfully'})
        except Expense.DoesNotExist:
            return JsonResponse({'error': 'Expense not found'}, status=404)

class PettyCashListView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/petty_cash_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get petty cash transactions from the database
        petty_cash_transactions = PettyCash.objects.all().order_by('-transaction_date', '-created_at')
        
        # Handle search functionality
        search_param = self.request.GET.get('search')
        if search_param:
            petty_cash_transactions = petty_cash_transactions.filter(
                Q(transaction_number__icontains=search_param) |
                Q(description__icontains=search_param) |
                Q(recipient__icontains=search_param)
            )
        
        # Handle status filter
        status_param = self.request.GET.get('status')
        if status_param:
            petty_cash_transactions = petty_cash_transactions.filter(status=status_param)
        
        # Handle transaction type filter
        transaction_type_param = self.request.GET.get('transaction_type')
        if transaction_type_param:
            petty_cash_transactions = petty_cash_transactions.filter(transaction_type=transaction_type_param)
        
        # Pagination
        paginator = Paginator(petty_cash_transactions, 10)  # Show 10 transactions per page
        page = self.request.GET.get('page')
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Initialize search form
        initial = {}
        if search_param:
            initial['search'] = search_param
        if status_param:
            initial['status'] = status_param
        if transaction_type_param:
            initial['transaction_type'] = transaction_type_param
        search_form = PettyCashFilterForm(initial=initial)
        
        context['petty_cash_transactions'] = page_obj
        context['page_obj'] = page_obj
        context['search_form'] = search_form
        
        return context

class PettyCashCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = PettyCashForm()
        # For HTMX requests, return only the modal content
        if request.headers.get('HX-Request'):
            return render(request, 'finance_management/modals/new_petty_cash_modal.html', {
                'form': form,
                'modal_id': 'new-modal'
            })
        # For non-HTMX requests, redirect to the main petty cash list page
        from django.shortcuts import redirect
        return redirect('finance_management:petty_cash_list')
    
    def post(self, request):
        form = PettyCashForm(request.POST, request.FILES)
        if form.is_valid():
            petty_cash = form.save(commit=False)
            petty_cash.created_by = request.user
            petty_cash.save()
            messages.success(request, 'Petty cash transaction created successfully.')
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:petty_cash_list')
            return response
        
        # Handle form errors for HTMX requests
        if request.headers.get('HX-Request'):
            return render(request, 'finance_management/modals/new_petty_cash_modal.html', {
                'form': form,
                'modal_id': 'new-modal'
            })
        # For non-HTMX requests, redirect to the main petty cash list page with error message
        from django.shortcuts import redirect
        messages.error(request, 'Please use the modal form to create petty cash transactions.')
        return redirect('finance_management:petty_cash_list')

class PettyCashDetailView(LoginRequiredMixin, DetailView):
    model = PettyCash
    template_name = 'finance_management/petty_cash_detail.html'
    context_object_name = 'petty_cash'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class PettyCashUpdateView(LoginRequiredMixin, UpdateView):
    model = PettyCash
    form_class = PettyCashForm
    template_name = 'finance_management/petty_cash_update.html'
    
    def get_success_url(self):
        return reverse_lazy('finance_management:petty_cash_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Petty cash transaction updated successfully.')
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse_lazy('finance_management:petty_cash_list')
        return response
    
    def form_invalid(self, form):
        # Handle form errors for HTMX requests
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'finance_management/modals/update_petty_cash_modal.html', {
                'form': form, 
                'petty_cash': self.object,
                'modal_id': 'update-petty-cash-modal'
            })
        return super().form_invalid(form)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        # For HTMX requests, return only the form content
        if request.headers.get('HX-Request'):
            return render(request, self.template_name, {'form': form, 'petty_cash': self.object})
        
        # For regular page requests, return the complete modal structure
        return render(request, 'finance_management/modals/update_petty_cash_modal.html', {
            'form': form, 
            'petty_cash': self.object,
            'modal_id': 'update-petty-cash-modal'
        })

class PettyCashDetailAPIView(LoginRequiredMixin, View):
    """API view to return petty cash details as JSON for modal population"""
    
    def get(self, request, pk):
        try:
            petty_cash = get_object_or_404(PettyCash, pk=pk)
            data = {
                'id': petty_cash.id,
                'transaction_number': petty_cash.transaction_number,
                'transaction_type': petty_cash.get_transaction_type_display(),
                'description': petty_cash.description,
                'amount': str(petty_cash.amount),
                'transaction_date': petty_cash.transaction_date.strftime('%Y-%m-%d'),
                'recipient': petty_cash.recipient,
                'purpose': petty_cash.purpose,
                'status': petty_cash.get_status_display(),
                'created_by': petty_cash.created_by.get_full_name() or petty_cash.created_by.username,
                'approved_by': petty_cash.approved_by.get_full_name() if petty_cash.approved_by else None,
                'created_at': petty_cash.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': petty_cash.updated_at.strftime('%Y-%m-%d %H:%M'),
                'receipt_url': petty_cash.receipt.url if petty_cash.receipt else None,
            }
            return JsonResponse(data)
        except PettyCash.DoesNotExist:
            return JsonResponse({'error': 'Petty cash transaction not found'}, status=404)

class PettyCashApprovalView(LoginRequiredMixin, View):
    """API view to approve a petty cash transaction"""
    
    def post(self, request, pk):
        try:
            petty_cash = get_object_or_404(PettyCash, pk=pk)
            petty_cash.status = 'APPROVED'
            petty_cash.approved_by = request.user
            petty_cash.save()
            
            messages.success(request, f'Petty cash transaction "{petty_cash.transaction_number}" has been approved.')
            return JsonResponse({'success': True, 'message': 'Petty cash transaction approved successfully'})
        except PettyCash.DoesNotExist:
            return JsonResponse({'error': 'Petty cash transaction not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class IncomeListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'finance_management/income_list.html'
    context_object_name = 'invoices'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Invoice.objects.select_related('client').all().order_by('-issue_date')
        
        # Handle search functionality
        search_param = self.request.GET.get('search')
        if search_param:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_param) |
                Q(client__name__icontains=search_param) |
                Q(status__icontains=search_param)
            )
        
        # Handle status filter
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Handle client filter
        client_filter = self.request.GET.get('client')
        if client_filter:
            queryset = queryset.filter(client_id=client_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create a simple search form context
        search_param = self.request.GET.get('search')
        context['search_form'] = {'search': search_param or ''}
        
        # Add clients for filter dropdown
        context['clients'] = Client.objects.all().order_by('name')
        
        return context

class ExpenseDetailAPIView(LoginRequiredMixin, View):
    """API view to return expense details as JSON for modal population"""
    
    def get(self, request, pk):
        try:
            expense = get_object_or_404(Expense, pk=pk)
            data = {
                'id': expense.id,
                'title': expense.title,
                'description': expense.description,
                'amount': str(expense.total_amount),
                'category': expense.expense_category.name if expense.expense_category else 'Uncategorized',
                'category_display': expense.expense_category.name if expense.expense_category else 'Uncategorized',
                'expense_date': expense.expense_date.strftime('%Y-%m-%d'),
                'created_by': expense.created_by.get_full_name() or expense.created_by.username,
                'approved_by': expense.approved_by.get_full_name() if expense.approved_by else None,
                'created_at': expense.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': expense.updated_at.strftime('%Y-%m-%d %H:%M'),
                'receipt_url': expense.receipt.url if expense.receipt else None,
            }
            return JsonResponse(data)
        except Expense.DoesNotExist:
            return JsonResponse({'error': 'Expense not found'}, status=404)

class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'finance_management/reports.html'
    context_object_name = 'reports'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Report.objects.select_related('generated_by').all().order_by('-created_at')
        
        # Handle search functionality
        search_param = self.request.GET.get('search')
        if search_param:
            queryset = queryset.filter(
                Q(name__icontains=search_param) |
                Q(report_type__icontains=search_param) |
                Q(description__icontains=search_param)
            )
        
        # Handle report type filter
        report_type_param = self.request.GET.get('report_type')
        if report_type_param:
            queryset = queryset.filter(report_type=report_type_param)
        
        # Handle status filter
        status_param = self.request.GET.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Handle format filter
        format_param = self.request.GET.get('format')
        if format_param:
            queryset = queryset.filter(format=format_param)
            
        return queryset
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests for report creation"""
        from .forms import ReportForm
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.urls import reverse
        from django.http import HttpResponse
        
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            
            # Generate report data immediately
            try:
                report_data = self.generate_report_data(
                    report.report_type,
                    report.start_date,
                    report.end_date,
                    {}
                )
                report.status = 'completed'
                report.data = report_data
            except Exception as e:
                report.status = 'failed'
                report.error_message = str(e)
            
            report.save()
            
            messages.success(request, 'Report generated successfully!')
            
            # Check if this is an HTMX request
            if request.headers.get('HX-Request'):
                response = HttpResponse(status=204)
                response['HX-Redirect'] = reverse('finance_management:reports')
                return response
            else:
                return redirect('finance_management:reports')
        else:
            messages.error(request, 'Please correct the errors in the form.')
            return self.get(request, *args, **kwargs)
    
    def generate_report_data(self, report_type, start_date, end_date, filters):
        """Generate report data based on report type"""
        # Import here to avoid circular imports
        from .views import ReportCreateView
        report_creator = ReportCreateView()
        return report_creator.generate_report_data(report_type, start_date, end_date, filters)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize search form with current filter values
        initial = {}
        search_param = self.request.GET.get('search')
        report_type_param = self.request.GET.get('report_type')
        status_param = self.request.GET.get('status')
        format_param = self.request.GET.get('format')
        
        if search_param:
            initial['search'] = search_param
        if report_type_param:
            initial['report_type'] = report_type_param
        if status_param:
            initial['status'] = status_param
        if format_param:
            initial['format'] = format_param
        
        search_form = ReportFilterForm(initial=initial)
        context['search_form'] = search_form
        
        return context

class ReportCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = ReportForm()
        return render(request, 'finance_management/modals/report_form.html', {
            'form': form,
            'modal_id': 'new-report-modal'
        })
    
    def post(self, request):
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            
            # Save additional filters based on report type
            filters = {}
            if report.report_type == 'petty_cash':
                if form.cleaned_data.get('petty_cash_status'):
                    filters['status'] = form.cleaned_data['petty_cash_status']
            elif report.report_type == 'expense':
                if form.cleaned_data.get('expense_category'):
                    filters['category'] = form.cleaned_data['expense_category']
            
            report.filters = filters
            report.save()
            
            messages.success(request, 'Report generation request submitted successfully.')
            
            # Check if this is an HTMX request (modal) or regular form submission
            if request.headers.get('HX-Request'):
                response = HttpResponse(status=204)
                response['HX-Redirect'] = reverse_lazy('finance_management:reports')
                return response
            else:
                # Regular form submission from page form
                return redirect('finance_management:reports')
        
        # If form is invalid, check if it's an HTMX request
        if request.headers.get('HX-Request'):
            return render(request, 'finance_management/modals/report_form.html', {
                'form': form,
                'modal_id': 'new-report-modal'
            })
        else:
            # For page form, redirect back to reports page with error
            messages.error(request, 'Please correct the errors below.')
            return redirect('finance_management:reports')

    def generate_report_data(self, report_type, start_date, end_date, filters=None):
        """Generate report data based on report type"""
        from django.db.models import Sum, Count, Avg
        from decimal import Decimal
        
        if report_type == 'cash_flow':
            return self.generate_cash_flow_report(start_date, end_date)
        elif report_type == 'profit_loss':
            return self.generate_profit_loss_report(start_date, end_date)
        elif report_type == 'balance_sheet':
            return self.generate_balance_sheet_report(start_date, end_date)
        elif report_type == 'accounts_receivable':
            return self.generate_ar_aging_report(start_date, end_date)
        elif report_type == 'accounts_payable':
            return self.generate_ap_aging_report(start_date, end_date)
        elif report_type == 'expense_analysis':
            return self.generate_expense_analysis_report(start_date, end_date)
        elif report_type == 'revenue_analysis':
            return self.generate_revenue_analysis_report(start_date, end_date)
        elif report_type == 'working_capital':
            return self.generate_working_capital_report(start_date, end_date)
        elif report_type == 'collection_performance':
            return self.generate_collection_performance_report(start_date, end_date)
        elif report_type == 'vendor_analysis':
            return self.generate_vendor_analysis_report(start_date, end_date)
        elif report_type == 'client_revenue':
            return self.generate_client_revenue_report(start_date, end_date)
        elif report_type == 'monthly_summary':
            return self.generate_monthly_summary_report(start_date, end_date)
        else:
            return {'error': 'Unknown report type'}

    def generate_cash_flow_report(self, start_date, end_date):
        """Generate Cash Flow Report"""
        # Operating Activities
        payments_received = Payment.objects.filter(
            payment_date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses_paid = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        ap_payments = AccountsPayable.objects.filter(
            status='PAID'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        net_operating_cash = payments_received - expenses_paid - ap_payments
        
        return {
            'report_type': 'Cash Flow Report',
            'period': f'{start_date} to {end_date}',
            'operating_activities': {
                'payments_received': float(payments_received),
                'expenses_paid': float(expenses_paid),
                'ap_payments': float(ap_payments),
                'net_operating_cash': float(net_operating_cash)
            },
            'cash_position': {
                'opening_balance': 0,  # Would need to track this
                'net_change': float(net_operating_cash),
                'closing_balance': float(net_operating_cash)
            }
        }

    def generate_profit_loss_report(self, start_date, end_date):
        """Generate Profit & Loss Statement"""
        # Revenue
        total_revenue = Payment.objects.filter(
            payment_date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Expenses
        total_expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status__in=['APPROVED', 'PAID']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Net Income
        net_income = total_revenue - total_expenses
        
        # Expense breakdown by category
        expense_by_category = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status__in=['APPROVED', 'PAID']
        ).values('expense_category__name').annotate(
            total=Sum('total_amount')
        ).order_by('-total')
        
        return {
            'report_type': 'Profit & Loss Statement',
            'period': f'{start_date} to {end_date}',
            'revenue': {
                'total_revenue': float(total_revenue)
            },
            'expenses': {
                'total_expenses': float(total_expenses),
                'by_category': [
                    {
                        'category': item['expense_category__name'] or 'Uncategorized',
                        'amount': float(item['total'])
                    } for item in expense_by_category
                ]
            },
            'net_income': float(net_income),
            'gross_margin': float((net_income / total_revenue * 100) if total_revenue > 0 else 0)
        }

    def generate_balance_sheet_report(self, start_date, end_date):
        """Generate Balance Sheet"""
        # Assets
        cash_position = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        accounts_receivable = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Liabilities
        accounts_payable = AccountsPayable.objects.filter(
            status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PARTIALLY_PAID']
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        # Equity (simplified)
        total_assets = cash_position + accounts_receivable
        total_liabilities = accounts_payable
        total_equity = total_assets - total_liabilities
        
        return {
            'report_type': 'Balance Sheet',
            'as_of_date': end_date,
            'assets': {
                'cash_and_equivalents': float(cash_position),
                'accounts_receivable': float(accounts_receivable),
                'total_assets': float(total_assets)
            },
            'liabilities': {
                'accounts_payable': float(accounts_payable),
                'total_liabilities': float(total_liabilities)
            },
            'equity': {
                'total_equity': float(total_equity)
            }
        }

    def generate_ar_aging_report(self, start_date, end_date):
        """Generate Accounts Receivable Aging Report"""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Group invoices by aging buckets
        current = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE'],
            due_date__gte=today
        ).aggregate(total=Sum('total'))['total'] or 0
        
        days_30 = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE'],
            due_date__lt=today,
            due_date__gte=today - timedelta(days=30)
        ).aggregate(total=Sum('total'))['total'] or 0
        
        days_60 = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE'],
            due_date__lt=today - timedelta(days=30),
            due_date__gte=today - timedelta(days=60)
        ).aggregate(total=Sum('total'))['total'] or 0
        
        days_90 = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE'],
            due_date__lt=today - timedelta(days=60),
            due_date__gte=today - timedelta(days=90)
        ).aggregate(total=Sum('total'))['total'] or 0
        
        over_90 = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE'],
            due_date__lt=today - timedelta(days=90)
        ).aggregate(total=Sum('total'))['total'] or 0
        
        total_ar = current + days_30 + days_60 + days_90 + over_90
        
        return {
            'report_type': 'Accounts Receivable Aging',
            'as_of_date': today,
            'aging_buckets': {
                'current': float(current),
                'days_30': float(days_30),
                'days_60': float(days_60),
                'days_90': float(days_90),
                'over_90': float(over_90),
                'total': float(total_ar)
            },
            'total_outstanding': float(total_ar)
        }

    def generate_ap_aging_report(self, start_date, end_date):
        """Generate Accounts Payable Aging Report"""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Group payables by aging buckets
        current = AccountsPayable.objects.filter(
            status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PARTIALLY_PAID'],
            due_date__gte=today
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        days_30 = AccountsPayable.objects.filter(
            status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PARTIALLY_PAID'],
            due_date__lt=today,
            due_date__gte=today - timedelta(days=30)
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        days_60 = AccountsPayable.objects.filter(
            status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PARTIALLY_PAID'],
            due_date__lt=today - timedelta(days=30),
            due_date__gte=today - timedelta(days=60)
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        over_60 = AccountsPayable.objects.filter(
            status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PARTIALLY_PAID'],
            due_date__lt=today - timedelta(days=60)
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        total_ap = current + days_30 + days_60 + over_60
        
        return {
            'report_type': 'Accounts Payable Aging',
            'as_of_date': today,
            'aging_buckets': {
                'current': float(current),
                'days_30': float(days_30),
                'days_60': float(days_60),
                'over_60': float(over_60),
                'total': float(total_ap)
            },
            'total_outstanding': float(total_ap)
        }

    def generate_expense_analysis_report(self, start_date, end_date):
        """Generate Expense Analysis Report"""
        # Total expenses
        total_expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status__in=['APPROVED', 'PAID']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Expenses by category
        expenses_by_category = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status__in=['APPROVED', 'PAID']
        ).values('expense_category__name').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Expenses by vendor
        expenses_by_vendor = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status__in=['APPROVED', 'PAID']
        ).values('vendor').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        return {
            'report_type': 'Expense Analysis Report',
            'period': f'{start_date} to {end_date}',
            'summary': {
                'total_expenses': float(total_expenses),
                'total_transactions': Expense.objects.filter(
                    expense_date__range=[start_date, end_date],
                    status__in=['APPROVED', 'PAID']
                ).count()
            },
            'by_category': [
                {
                    'category': item['expense_category__name'] or 'Uncategorized',
                    'amount': float(item['total']),
                    'count': item['count'],
                    'percentage': float((item['total'] / total_expenses * 100) if total_expenses > 0 else 0)
                } for item in expenses_by_category
            ],
            'by_vendor': [
                {
                    'vendor': item['vendor'],
                    'amount': float(item['total']),
                    'count': item['count']
                } for item in expenses_by_vendor
            ]
        }

    def generate_revenue_analysis_report(self, start_date, end_date):
        """Generate Revenue Analysis Report"""
        # Total revenue
        total_revenue = Payment.objects.filter(
            payment_date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Revenue by client
        revenue_by_client = Payment.objects.filter(
            payment_date__range=[start_date, end_date]
        ).values('invoice__client__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Revenue by payment method
        revenue_by_method = Payment.objects.filter(
            payment_date__range=[start_date, end_date]
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return {
            'report_type': 'Revenue Analysis Report',
            'period': f'{start_date} to {end_date}',
            'summary': {
                'total_revenue': float(total_revenue),
                'total_payments': Payment.objects.filter(
                    payment_date__range=[start_date, end_date]
                ).count()
            },
            'by_client': [
                {
                    'client': item['invoice__client__name'] or 'Unknown Client',
                    'amount': float(item['total']),
                    'count': item['count'],
                    'percentage': float((item['total'] / total_revenue * 100) if total_revenue > 0 else 0)
                } for item in revenue_by_client
            ],
            'by_payment_method': [
                {
                    'method': item['payment_method'],
                    'amount': float(item['total']),
                    'count': item['count']
                } for item in revenue_by_method
            ]
        }

    def generate_working_capital_report(self, start_date, end_date):
        """Generate Working Capital Report"""
        # Current Assets
        cash_position = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        accounts_receivable = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Current Liabilities
        accounts_payable = AccountsPayable.objects.filter(
            status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PARTIALLY_PAID']
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        # Working Capital
        current_assets = cash_position + accounts_receivable
        current_liabilities = accounts_payable
        working_capital = current_assets - current_liabilities
        
        # Working Capital Ratio
        working_capital_ratio = (current_assets / current_liabilities) if current_liabilities > 0 else 0
        
        return {
            'report_type': 'Working Capital Report',
            'as_of_date': end_date,
            'current_assets': {
                'cash_and_equivalents': float(cash_position),
                'accounts_receivable': float(accounts_receivable),
                'total_current_assets': float(current_assets)
            },
            'current_liabilities': {
                'accounts_payable': float(accounts_payable),
                'total_current_liabilities': float(current_liabilities)
            },
            'working_capital': {
                'working_capital': float(working_capital),
                'working_capital_ratio': float(working_capital_ratio)
            }
        }

    def generate_collection_performance_report(self, start_date, end_date):
        """Generate Collection Performance Report"""
        # Collection metrics
        total_invoices = Invoice.objects.count()
        paid_invoices = Invoice.objects.filter(status='PAID').count()
        overdue_invoices = Invoice.objects.filter(status='OVERDUE').count()
        
        # Collection rate
        collection_rate = (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
        
        # Average payment time
        paid_payments = Payment.objects.filter(payment_date__isnull=False)
        if paid_payments.exists():
            total_days = 0
            payment_count = 0
            for payment in paid_payments:
                if payment.invoice and payment.invoice.issue_date:
                    days_diff = (payment.payment_date - payment.invoice.issue_date).days
                    if days_diff >= 0:
                        total_days += days_diff
                        payment_count += 1
            
            avg_payment_time = total_days / payment_count if payment_count > 0 else 0
        else:
            avg_payment_time = 0
        
        # Outstanding amounts
        outstanding_amount = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        return {
            'report_type': 'Collection Performance Report',
            'period': f'{start_date} to {end_date}',
            'collection_metrics': {
                'total_invoices': total_invoices,
                'paid_invoices': paid_invoices,
                'overdue_invoices': overdue_invoices,
                'collection_rate': float(collection_rate),
                'avg_payment_time': float(avg_payment_time),
                'outstanding_amount': float(outstanding_amount)
            }
        }

    def generate_vendor_analysis_report(self, start_date, end_date):
        """Generate Vendor Analysis Report"""
        # Vendor spending
        vendor_spending = AccountsPayable.objects.filter(
            invoice_date__range=[start_date, end_date]
        ).values('vendor').annotate(
            total_amount=Sum('total_amount'),
            total_paid=Sum('amount_paid'),
            count=Count('id')
        ).order_by('-total_amount')
        
        # Vendor payment performance
        vendor_performance = []
        for vendor in vendor_spending:
            vendor_name = vendor['vendor']
            total_amount = vendor['total_amount']
            total_paid = vendor['total_paid']
            payment_rate = (total_paid / total_amount * 100) if total_amount > 0 else 0
            
            vendor_performance.append({
                'vendor': vendor_name,
                'total_amount': float(total_amount),
                'total_paid': float(total_paid),
                'outstanding': float(total_amount - total_paid),
                'payment_rate': float(payment_rate),
                'transaction_count': vendor['count']
            })
        
        return {
            'report_type': 'Vendor Analysis Report',
            'period': f'{start_date} to {end_date}',
            'vendor_performance': vendor_performance
        }

    def generate_client_revenue_report(self, start_date, end_date):
        """Generate Client Revenue Report"""
        # Client revenue
        client_revenue = Payment.objects.filter(
            payment_date__range=[start_date, end_date]
        ).values('invoice__client__name').annotate(
            total_revenue=Sum('amount'),
            payment_count=Count('id')
        ).order_by('-total_revenue')
        
        # Client outstanding amounts
        client_outstanding = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE']
        ).values('client__name').annotate(
            outstanding_amount=Sum('total'),
            invoice_count=Count('id')
        ).order_by('-outstanding_amount')
        
        return {
            'report_type': 'Client Revenue Report',
            'period': f'{start_date} to {end_date}',
            'client_revenue': [
                {
                    'client': item['invoice__client__name'] or 'Unknown Client',
                    'revenue': float(item['total_revenue']),
                    'payment_count': item['payment_count']
                } for item in client_revenue
            ],
            'client_outstanding': [
                {
                    'client': item['client__name'] or 'Unknown Client',
                    'outstanding': float(item['outstanding_amount']),
                    'invoice_count': item['invoice_count']
                } for item in client_outstanding
            ]
        }

    def generate_monthly_summary_report(self, start_date, end_date):
        """Generate Monthly Financial Summary"""
        # Monthly revenue
        monthly_revenue = Payment.objects.filter(
            payment_date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Monthly expenses
        monthly_expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status__in=['APPROVED', 'PAID']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Net income
        net_income = monthly_revenue - monthly_expenses
        
        # Key metrics
        collection_rate = 0
        if Invoice.objects.count() > 0:
            collection_rate = (Invoice.objects.filter(status='PAID').count() / Invoice.objects.count()) * 100
        
        return {
            'report_type': 'Monthly Financial Summary',
            'period': f'{start_date} to {end_date}',
            'summary': {
                'total_revenue': float(monthly_revenue),
                'total_expenses': float(monthly_expenses),
                'net_income': float(net_income),
                'collection_rate': float(collection_rate),
                'profit_margin': float((net_income / monthly_revenue * 100) if monthly_revenue > 0 else 0)
            }
        }

class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'finance_management/report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class ReportPreviewView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'finance_management/report_preview.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        
        # Generate report data using the ReportCreateView methods
        report_creator = ReportCreateView()
        report_data = report_creator.generate_report_data(
            report.report_type, 
            report.start_date, 
            report.end_date, 
            report.filters
        )
        
        context['report_data'] = report_data
        return context

class ReportDetailAPIView(LoginRequiredMixin, View):
    """API view to return report details as JSON for modal population"""
    
    def get(self, request, pk):
        try:
            report = get_object_or_404(Report, pk=pk)
            data = {
                'id': report.id,
                'name': report.name,
                'report_type': report.get_report_type_display(),
                'date_range': report.date_range,
                'format': report.get_format_display(),
                'status': report.get_status_display(),
                'description': report.description,
                'file_size': report.file_size_formatted,
                'generated_by': report.generated_by.get_full_name() or report.generated_by.username,
                'created_at': report.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': report.updated_at.strftime('%Y-%m-%d %H:%M'),
                'file_path': report.file_path,
            }
            return JsonResponse(data)
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)

class ReportDownloadView(LoginRequiredMixin, View):
    """View to handle report downloads"""
    
    def get(self, request, pk):
        try:
            report = get_object_or_404(Report, pk=pk)
            
            # Handle different report statuses
            if report.status == 'failed':
                messages.error(request, 'Report generation failed. Please try generating the report again.')
                return JsonResponse({'error': 'Report generation failed'}, status=400)
            elif report.status == 'pending':
                # Update status to processing and simulate report generation
                report.status = 'processing'
                report.save()
                messages.info(request, f'Report "{report.name}" is being generated. Please wait a moment and try again.')
                return JsonResponse({'info': 'Report is being generated'}, status=202)
            elif report.status == 'processing':
                # Simulate completion for demo purposes
                report.status = 'completed'
                report.file_path = f'reports/{report.name.replace(" ", "_").lower()}_{report.pk}.pdf'
                report.save()
                messages.success(request, f'Report "{report.name}" has been generated and download started.')
                return JsonResponse({'success': True, 'message': 'Report generated and download started'})
            elif report.status == 'completed':
                # Report is ready for download
                messages.success(request, f'Report "{report.name}" download started.')
                return JsonResponse({'success': True, 'message': 'Download started'})
            else:
                messages.error(request, 'Report status is unknown.')
                return JsonResponse({'error': 'Unknown report status'}, status=400)
            
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)

class AccountDeleteView(LoginRequiredMixin, View):
    """View to handle account deletion"""
    
    def post(self, request, code):
        try:
            account = get_object_or_404(Account, code=code)
            account_name = account.name
            account.delete()
            
            messages.success(request, f'Account "{account_name}" has been deleted successfully.')
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:chart_of_accounts')
            return response
            
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)

class ReportDeleteView(LoginRequiredMixin, View):
    """View to handle report deletion"""
    
    def post(self, request, pk):
        try:
            report = get_object_or_404(Report, pk=pk)
            report_name = report.name
            report.delete()
            
            messages.success(request, f'Report "{report_name}" has been deleted successfully.')
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:reports')
            return response
            
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)

class ExpenseReportView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/expense_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request parameters
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')
        
        # Default to current month if no dates specified
        if not from_date or not to_date:
            today = timezone.now()
            from_date = today.replace(day=1).date()
            to_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        
        # Get expenses for the date range
        expenses = Expense.objects.filter(
            expense_date__range=[from_date, to_date]
        ).select_related('client_case', 'account', 'submitted_by', 'approved_by')
        
        # Calculate summary statistics
        total_expenses = expenses.aggregate(total=Sum('total_amount'))['total'] or 0
        # Note: billable_status field was removed, using total expenses instead
        billable_expenses = 0  # Placeholder - billable functionality removed
        non_billable_expenses = total_expenses  # All expenses are now non-billable by default
        pending_expenses = expenses.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']).count()
        
        # Calculate expenses by category
        category_expenses = {}
        for expense in expenses:
            category = expense.expense_category.name if expense.expense_category else 'Uncategorized'
            if category not in category_expenses:
                category_expenses[category] = {
                    'amount': 0,
                    'billable': 0,
                    'non_billable': 0,
                    'count': 0
                }
            
            category_expenses[category]['amount'] += expense.total_amount
            category_expenses[category]['count'] += 1
            
            # Note: billable functionality removed, all expenses are non-billable
            category_expenses[category]['billable'] += 0
            category_expenses[category]['non_billable'] += expense.total_amount
        
        # Calculate compliance statistics
        compliant_expenses = expenses.filter(is_compliant=True).count()
        total_expense_count = expenses.count()
        compliance_rate = (compliant_expenses / total_expense_count * 100) if total_expense_count > 0 else 0
        
        # Add context data
        context.update({
            'from_date': from_date,
            'to_date': to_date,
            'total_expenses': total_expenses,
            'billable_expenses': billable_expenses,
            'non_billable_expenses': non_billable_expenses,
            'pending_expenses': pending_expenses,
            'category_expenses': category_expenses,
            'compliance_rate': compliance_rate,
            'compliant_expenses': compliant_expenses,
            'total_expense_count': total_expense_count,
            'expenses': expenses,
        })
        
        return context

# New Accounting Views

class JournalListView(LoginRequiredMixin, ListView):
    model = Journal
    template_name = 'finance_management/journal_list.html'
    context_object_name = 'journals'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Journal.objects.all()
        status = self.request.GET.get('status')
        journal_type = self.request.GET.get('journal_type')
        
        if status:
            queryset = queryset.filter(status=status)
        if journal_type:
            queryset = queryset.filter(journal_type=journal_type)
            
        return queryset.order_by('code')

class JournalCreateView(LoginRequiredMixin, CreateView):
    model = Journal
    form_class = JournalForm
    template_name = 'finance_management/journal_form.html'
    success_url = reverse_lazy('finance_management:journal_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Journal created successfully.')
        return super().form_valid(form)

class JournalUpdateView(LoginRequiredMixin, UpdateView):
    model = Journal
    form_class = JournalForm
    template_name = 'finance_management/journal_form.html'
    success_url = reverse_lazy('finance_management:journal_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Journal updated successfully.')
        return super().form_valid(form)

class JournalDeleteView(LoginRequiredMixin, DeleteView):
    model = Journal
    template_name = 'finance_management/journal_confirm_delete.html'
    success_url = reverse_lazy('finance_management:journal_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Journal deleted successfully.')
        return super().delete(request, *args, **kwargs)

class AccountingPeriodListView(LoginRequiredMixin, ListView):
    model = AccountingPeriod
    template_name = 'finance_management/period_list.html'
    context_object_name = 'periods'
    paginate_by = 20
    
    def get_queryset(self):
        return AccountingPeriod.objects.all().order_by('-start_date')

class AccountingPeriodCreateView(LoginRequiredMixin, CreateView):
    model = AccountingPeriod
    form_class = AccountingPeriodForm
    template_name = 'finance_management/period_form.html'
    success_url = reverse_lazy('finance_management:period_list')
    
    def form_valid(self, form):
        # Ensure only one current period exists
        if form.cleaned_data['is_current']:
            AccountingPeriod.objects.filter(is_current=True).update(is_current=False)
        
        messages.success(self.request, 'Accounting period created successfully.')
        return super().form_valid(form)

class AccountingPeriodUpdateView(LoginRequiredMixin, UpdateView):
    model = AccountingPeriod
    form_class = AccountingPeriodForm
    template_name = 'finance_management/period_form.html'
    success_url = reverse_lazy('finance_management:period_list')
    
    def form_valid(self, form):
        # Ensure only one current period exists
        if form.cleaned_data['is_current']:
            AccountingPeriod.objects.filter(is_current=True).update(is_current=False)
        
        messages.success(self.request, 'Accounting period updated successfully.')
        return super().form_valid(form)

class AccountingPeriodDetailView(LoginRequiredMixin, DetailView):
    model = AccountingPeriod
    template_name = 'finance_management/period_detail.html'
    context_object_name = 'period'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.get_object()
        
        # Get journal entries for this period
        context['journal_entries'] = period.journal_entries.all().order_by('-date')
        
        # Get account balances for this period
        context['account_balances'] = period.account_balances.all().order_by('account__code')
        
        # Calculate period summary
        total_debits = period.journal_entries.filter(status='POSTED').aggregate(
            total=Sum('total_debit'))['total'] or Decimal('0.00')
        total_credits = period.journal_entries.filter(status='POSTED').aggregate(
            total=Sum('total_credit'))['total'] or Decimal('0.00')
        
        context['total_debits'] = total_debits
        context['total_credits'] = total_credits
        context['is_balanced'] = total_debits == total_credits
        
        return context

class PeriodClosingView(LoginRequiredMixin, View):
    template_name = 'finance_management/period_closing.html'
    
    def get(self, request):
        form = PeriodClosingForm()
        periods = AccountingPeriod.objects.filter(status='OPEN')
        return render(request, self.template_name, {'form': form, 'periods': periods})
    
    def post(self, request):
        form = PeriodClosingForm(request.POST)
        if form.is_valid():
            period = form.cleaned_data['period']
            closing_notes = form.cleaned_data['closing_notes']
            
            try:
                period.close_period(request.user, closing_notes)
                messages.success(request, f'Period {period.name} closed successfully.')
                return redirect('finance_management:period_detail', pk=period.pk)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Please correct the errors below.')
        
        periods = AccountingPeriod.objects.filter(status='OPEN')
        return render(request, self.template_name, {'form': form, 'periods': periods})

class EnhancedJournalEntryListView(LoginRequiredMixin, ListView):
    model = JournalEntry
    template_name = 'finance_management/enhanced_journal_entry_list.html'
    context_object_name = 'journal_entries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = JournalEntry.objects.select_related('journal', 'period', 'created_by')
        
        # Apply filters
        journal = self.request.GET.get('journal')
        period = self.request.GET.get('period')
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')
        
        if journal:
            queryset = queryset.filter(journal_id=journal)
        if period:
            queryset = queryset.filter(period_id=period)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) | 
                Q(reference__icontains=search)
            )
        
        return queryset.order_by('-date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = JournalEntryFilterForm(self.request.GET)
        context['journals'] = Journal.objects.filter(status='ACTIVE')
        context['periods'] = AccountingPeriod.objects.all()
        return context

class EnhancedJournalEntryCreateView(LoginRequiredMixin, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'finance_management/enhanced_journal_entry_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines_formset'] = JournalEntryLineFormSet(self.request.POST, instance=self.object)
        else:
            context['lines_formset'] = JournalEntryLineFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context['lines_formset']
        
        if form.is_valid() and lines_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            
            # Calculate totals
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            
            for line_form in lines_formset:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE'):
                    debit = line_form.cleaned_data.get('debit') or Decimal('0.00')
                    credit = line_form.cleaned_data.get('credit') or Decimal('0.00')
                    total_debit += debit
                    total_credit += credit
            
            self.object.total_debit = total_debit
            self.object.total_credit = total_credit
            
            self.object.save()
            lines_formset.instance = self.object
            lines_formset.save()
            
            messages.success(self.request, 'Journal entry created successfully.')
            return redirect('finance_management:enhanced_journal_entry_detail', pk=self.object.pk)
        
        return self.render_to_response(self.get_context_data(form=form))

class EnhancedJournalEntryDetailView(LoginRequiredMixin, DetailView):
    model = JournalEntry
    template_name = 'finance_management/enhanced_journal_entry_detail.html'
    context_object_name = 'journal_entry'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all().order_by('id')
        return context

class EnhancedJournalEntryUpdateView(LoginRequiredMixin, UpdateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'finance_management/enhanced_journal_entry_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines_formset'] = JournalEntryLineFormSet(self.request.POST, instance=self.object)
        else:
            context['lines_formset'] = JournalEntryLineFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context['lines_formset']
        
        if form.is_valid() and lines_formset.is_valid():
            self.object = form.save(commit=False)
            
            # Calculate totals
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            
            for line_form in lines_formset:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE'):
                    debit = line_form.cleaned_data.get('debit') or Decimal('0.00')
                    credit = line_form.cleaned_data.get('credit') or Decimal('0.00')
                    total_debit += debit
                    total_credit += credit
            
            self.object.total_debit = total_debit
            self.object.total_credit = total_credit
            
            self.object.save()
            lines_formset.instance = self.object
            lines_formset.save()
            
            messages.success(self.request, 'Journal entry updated successfully.')
            return redirect('finance_management:enhanced_journal_entry_detail', pk=self.object.pk)
        
        return self.render_to_response(self.get_context_data(form=form))

class JournalEntryPostView(LoginRequiredMixin, View):
    def post(self, request, pk):
        journal_entry = get_object_or_404(JournalEntry, pk=pk)
        
        try:
            journal_entry.post_entry(request.user)
            messages.success(request, 'Journal entry posted successfully.')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('finance_management:enhanced_journal_entry_detail', pk=pk)

class JournalEntryReverseView(LoginRequiredMixin, View):
    def post(self, request, pk):
        journal_entry = get_object_or_404(JournalEntry, pk=pk)
        reason = request.POST.get('reason', '')
        
        try:
            reversing_entry = journal_entry.reverse_entry(request.user, reason)
            messages.success(request, f'Journal entry reversed. Reversing entry: {reversing_entry.entry_number}')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('finance_management:enhanced_journal_entry_detail', pk=pk)

# Financial Reporting Views

class TrialBalanceView(LoginRequiredMixin, View):
    template_name = 'finance_management/trial_balance.html'
    
    def get(self, request):
        form = FinancialStatementForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = FinancialStatementForm(request.POST)
        if form.is_valid():
            period = form.cleaned_data['period']
            as_of_date = form.cleaned_data['as_of_date']
            
            # Get all active accounts with balances
            accounts = Account.objects.filter(status='ACTIVE').order_by('code')
            trial_balance_data = []
            
            total_debits = Decimal('0.00')
            total_credits = Decimal('0.00')
            
            for account in accounts:
                balance = account.get_balance_as_of_date(as_of_date)
                
                if balance != 0:
                    if account.normal_balance == 'DEBIT':
                        debit = balance
                        credit = Decimal('0.00')
                    else:
                        debit = Decimal('0.00')
                        credit = abs(balance)
                    
                    trial_balance_data.append({
                        'account': account,
                        'debit': debit,
                        'credit': credit,
                        'balance': balance
                    })
                    
                    total_debits += debit
                    total_credits += credit
            
            context = {
                'form': form,
                'trial_balance_data': trial_balance_data,
                'total_debits': total_debits,
                'total_credits': total_credits,
                'is_balanced': total_debits == total_credits,
                'period': period,
                'as_of_date': as_of_date
            }
            
            return render(request, self.template_name, context)
        
        return render(request, self.template_name, {'form': form})

class BalanceSheetView(LoginRequiredMixin, View):
    template_name = 'finance_management/balance_sheet.html'
    
    def get(self, request):
        form = FinancialStatementForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = FinancialStatementForm(request.POST)
        if form.is_valid():
            period = form.cleaned_data['period']
            as_of_date = form.cleaned_data['as_of_date']
            
            # Get assets
            assets = Account.objects.filter(
                account_type='ASSET', 
                status='ACTIVE'
            ).order_by('code')
            
            # Get liabilities
            liabilities = Account.objects.filter(
                account_type='LIABILITY', 
                status='ACTIVE'
            ).order_by('code')
            
            # Get equity
            equity = Account.objects.filter(
                account_type='EQUITY', 
                status='ACTIVE'
            ).order_by('code')
            
            # Calculate totals
            total_assets = sum(acc.get_balance_as_of_date(as_of_date) for acc in assets)
            total_liabilities = sum(acc.get_balance_as_of_date(as_of_date) for acc in liabilities)
            total_equity = sum(acc.get_balance_as_of_date(as_of_date) for acc in equity)
            
            context = {
                'form': form,
                'assets': assets,
                'liabilities': liabilities,
                'equity': equity,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_equity': total_equity,
                'period': period,
                'as_of_date': as_of_date
            }
            
            return render(request, self.template_name, context)
        
        return render(request, self.template_name, {'form': form})

class IncomeStatementView(LoginRequiredMixin, View):
    template_name = 'finance_management/income_statement.html'
    
    def get(self, request):
        form = FinancialStatementForm(request.GET)
        if form.is_valid():
            statement_type = form.cleaned_data['statement_type']
            period = form.cleaned_data['period']
            as_of_date = form.cleaned_data['as_of_date']
            format_type = form.cleaned_data['format']
            
            # Generate income statement data
            data = self.generate_income_statement(period, as_of_date)
            
            if format_type == 'JSON':
                return JsonResponse(data)
            else:
                context = {
                    'form': form,
                    'data': data,
                    'period': period,
                    'as_of_date': as_of_date,
                }
                return render(request, self.template_name, context)
        
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def generate_income_statement(self, period, as_of_date):
        """Generate income statement data"""
        # Get revenue accounts
        revenue_accounts = Account.objects.filter(
            account_type='REVENUE',
            is_active=True
        )
        
        # Get expense accounts
        expense_accounts = Account.objects.filter(
            account_type='EXPENSE',
            is_active=True
        )
        
        # Calculate balances
        revenue_total = sum(
            account.get_balance_as_of_date(as_of_date) 
            for account in revenue_accounts
        )
        
        expense_total = sum(
            account.get_balance_as_of_date(as_of_date) 
            for account in expense_accounts
        )
        
        net_income = revenue_total - expense_total
        
        return {
            'revenue_accounts': [
                {
                    'name': account.name,
                    'balance': account.get_balance_as_of_date(as_of_date)
                }
                for account in revenue_accounts
            ],
            'expense_accounts': [
                {
                    'name': account.name,
                    'balance': account.get_balance_as_of_date(as_of_date)
                }
                for account in expense_accounts
            ],
            'revenue_total': revenue_total,
            'expense_total': expense_total,
            'net_income': net_income,
        }


# Expense Management Views
class ExpenseCategoryListView(LoginRequiredMixin, ListView):
    model = ExpenseCategory
    template_name = 'finance_management/expense_category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ExpenseCategory.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class ExpenseCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'finance_management/expense_category_form.html'
    success_url = reverse_lazy('finance_management:expense_category_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Expense category created successfully.')
        return super().form_valid(form)


class ExpenseCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'finance_management/expense_category_form.html'
    success_url = reverse_lazy('finance_management:expense_category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Expense category updated successfully.')
        return super().form_valid(form)


class ExpenseCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ExpenseCategory
    template_name = 'finance_management/expense_category_confirm_delete.html'
    success_url = reverse_lazy('finance_management:expense_category_list')
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        if category.expense_set.exists():
            messages.error(request, 'Cannot delete category with associated expenses.')
            return redirect('finance_management:expense_category_list')
        
        messages.success(request, 'Expense category deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'finance_management/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = None  # TEMPORARILY DISABLE PAGINATION FOR DEBUGGING
    
    def get_paginate_by(self, queryset):
        # Debug pagination
        print(f"DEBUG: Paginate by: {self.paginate_by}")
        print(f"DEBUG: Queryset count: {queryset.count()}")
        return self.paginate_by
    

    
    def get_queryset(self):
        # Debug: Check all expenses first
        all_expenses = Expense.objects.all()
        print(f"DEBUG: Total expenses in database: {all_expenses.count()}")
        if all_expenses.exists():
            print(f"DEBUG: First expense: {all_expenses.first()}")
            print(f"DEBUG: First expense fields: {[f.name for f in all_expenses.first()._meta.fields]}")
        
        queryset = Expense.objects.select_related(
            'expense_category', 'period', 'created_by'
        ).all()
        
        print(f"DEBUG: Queryset before filtering: {queryset.count()}")
        
        form = ExpenseFilterForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data
            print(f"DEBUG: Form data: {data}")
            
            if data.get('search'):
                queryset = queryset.filter(
                    Q(title__icontains=data['search']) |
                    Q(description__icontains=data['search']) |
                    Q(vendor__icontains=data['search']) |
                    Q(reference_number__icontains=data['search'])
                )
                print(f"DEBUG: After search filter: {queryset.count()}")
            
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
                print(f"DEBUG: After status filter: {queryset.count()}")
            
            if data.get('expense_type'):
                queryset = queryset.filter(expense_type=data['expense_type'])
                print(f"DEBUG: After expense_type filter: {queryset.count()}")
            
            if data.get('expense_category'):
                queryset = queryset.filter(expense_category=data['expense_category'])
                print(f"DEBUG: After expense_category filter: {queryset.count()}")
            
            if data.get('period'):
                queryset = queryset.filter(period=data['period'])
                print(f"DEBUG: After period filter: {queryset.count()}")
            
            if data.get('date_from'):
                queryset = queryset.filter(expense_date__gte=data['date_from'])
                print(f"DEBUG: After date_from filter: {queryset.count()}")
            
            if data.get('date_to'):
                queryset = queryset.filter(expense_date__lte=data['date_to'])
                print(f"DEBUG: After date_to filter: {queryset.count()}")
            
            if data.get('vendor'):
                queryset = queryset.filter(vendor__icontains=data['vendor'])
                print(f"DEBUG: After vendor filter: {queryset.count()}")
            
            if data.get('min_amount'):
                queryset = queryset.filter(total_amount__gte=data['min_amount'])
                print(f"DEBUG: After min_amount filter: {queryset.count()}")
            
            if data.get('max_amount'):
                queryset = queryset.filter(total_amount__lte=data['max_amount'])
                print(f"DEBUG: After max_amount filter: {queryset.count()}")
        else:
            print(f"DEBUG: Form errors: {form.errors}")
        
        final_queryset = queryset.order_by('-expense_date', '-created_at')
        print(f"DEBUG: Final queryset count: {final_queryset.count()}")
        print(f"DEBUG: Final queryset type: {type(final_queryset)}")
        print(f"DEBUG: Final queryset SQL: {str(final_queryset.query)[:200]}...")
        return final_queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the base queryset for calculations
        base_queryset = self.get_queryset()
        
        # Debug: Check what's in the context
        print(f"DEBUG: Context keys: {list(context.keys())}")
        print(f"DEBUG: Context object_list: {len(context.get('object_list', []))}")
        print(f"DEBUG: Context expenses: {len(context.get('expenses', []))}")
        print(f"DEBUG: Context page_obj: {context.get('page_obj')}")
        
        # CRITICAL FIX: Ensure expenses are properly set
        # Django ListView sets object_list, but context_object_name might not be working
        if 'expenses' not in context or not context['expenses']:
            # Get expenses from object_list or page_obj.object_list
            if 'page_obj' in context and hasattr(context['page_obj'], 'object_list'):
                context['expenses'] = context['page_obj'].object_list
                print(f"DEBUG: Set expenses from page_obj.object_list: {len(context['expenses'])}")
            elif 'object_list' in context:
                context['expenses'] = context['object_list']
                print(f"DEBUG: Set expenses from object_list: {len(context['expenses'])}")
            else:
                # Fallback: get expenses directly from queryset
                context['expenses'] = list(base_queryset[:20])  # First 20 for pagination
                print(f"DEBUG: Set expenses from base_queryset: {len(context['expenses'])}")
        
        context['filter_form'] = ExpenseFilterForm(self.request.GET)
        context['total_expenses'] = base_queryset.count()
        context['total_amount'] = base_queryset.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Status counts
        status_counts = {}
        for status, _ in Expense.EXPENSE_STATUS_CHOICES:
            status_counts[status] = base_queryset.filter(status=status).count()
        context['status_counts'] = status_counts
        
        # Add data for expense creation modal
        context['expense_categories'] = ExpenseCategory.objects.filter(is_active=True).order_by('name')
        context['accounting_periods'] = AccountingPeriod.objects.filter(status='OPEN').order_by('-start_date')
        
        # ADDITIONAL DEBUG: Check pagination objects
        if 'page_obj' in context:
            print(f"DEBUG: page_obj type: {type(context['page_obj'])}")
            print(f"DEBUG: page_obj has object_list: {hasattr(context['page_obj'], 'object_list')}")
            if hasattr(context['page_obj'], 'object_list'):
                print(f"DEBUG: page_obj.object_list type: {type(context['page_obj'].object_list)}")
                print(f"DEBUG: page_obj.object_list count: {len(context['page_obj'].object_list)}")
                print(f"DEBUG: page_obj.object_list first item: {context['page_obj'].object_list[0] if context['page_obj'].object_list else 'None'}")
        
        # ULTIMATE FALLBACK: If still no expenses, get them directly
        if not context.get('expenses') or len(context['expenses']) == 0:
            print("DEBUG: ULTIMATE FALLBACK - Getting expenses directly from queryset")
            
            # DIRECT DATABASE ACCESS TEST
            direct_expenses = list(Expense.objects.all())
            print(f"DEBUG: Direct database access - Count: {len(direct_expenses)}")
            if direct_expenses:
                print(f"DEBUG: Direct first expense: {direct_expenses[0]}")
                print(f"DEBUG: Direct expense IDs: {[e.id for e in direct_expenses[:5]]}")
            
            # TEMPORARILY: Get ALL expenses for debugging (bypass pagination)
            context['expenses'] = list(base_queryset)
            print(f"DEBUG: Fallback expenses count: {len(context['expenses'])}")
            print(f"DEBUG: Fallback expenses type: {type(context['expenses'])}")
            if context['expenses']:
                print(f"DEBUG: Fallback first expense: {context['expenses'][0]}")
                print(f"DEBUG: Fallback last expense: {context['expenses'][-1]}")
                print(f"DEBUG: All expense IDs: {[e.id for e in context['expenses']]}")
            else:
                print("DEBUG: Fallback failed - base_queryset is empty!")
                # Use direct database access as final fallback
                context['expenses'] = direct_expenses
                print(f"DEBUG: Final fallback using direct DB access: {len(context['expenses'])}")
        
        print(f"DEBUG: Final context expenses count: {len(context.get('expenses', []))}")
        print(f"DEBUG: Final context expenses type: {type(context.get('expenses'))}")
        if context.get('expenses'):
            print(f"DEBUG: First expense in context: {context['expenses'][0] if context['expenses'] else 'None'}")
        
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance_management/expense_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['line_items_formset'] = ExpenseLineItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['line_items_formset'] = ExpenseLineItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        line_items_formset = context['line_items_formset']
        
        if form.is_valid() and line_items_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            
            # Auto-calculate net amount
            if self.object.total_amount and self.object.tax_amount:
                self.object.net_amount = self.object.total_amount - self.object.tax_amount
            
            self.object.save()
            
            # Save line items
            line_items_formset.instance = self.object
            line_items_formset.save()
            
            # Create journal entry
            if self.object.period:
                self.object.create_journal_entry()
            
            # Check if this is an AJAX request
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Expense created successfully!',
                    'expense_id': self.object.pk,
                    'redirect_url': reverse('finance_management:expense_detail', kwargs={'pk': self.object.pk})
                })
            
            messages.success(self.request, 'Expense created successfully.')
            return redirect('finance_management:expense_detail', pk=self.object.pk)
        
        # Handle form errors for AJAX requests
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors[0] if field_errors else 'Invalid input'
            
            return JsonResponse({
                'success': False,
                'error': 'Please correct the errors below.',
                'field_errors': errors
            })
        
        return self.render_to_response(self.get_context_data(form=form))


class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'finance_management/expense_detail.html'
    context_object_name = 'expense'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['approval_form'] = ExpenseApprovalForm(expense=self.object)
        context['payment_form'] = ExpensePaymentForm(expense=self.object)
        return context


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance_management/expense_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['line_items_formset'] = ExpenseLineItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['line_items_formset'] = ExpenseLineItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        line_items_formset = context['line_items_formset']
        
        if form.is_valid() and line_items_formset.is_valid():
            self.object = form.save(commit=False)
            
            # Auto-calculate net amount
            if self.object.total_amount and self.object.tax_amount:
                self.object.net_amount = self.object.total_amount - self.object.tax_amount
            
            self.object.save()
            
            # Save line items
            line_items_formset.instance = self.object
            line_items_formset.save()
            
            # Update journal entry if period changed
            if self.object.period and not self.object.journal_entry:
                self.object.create_journal_entry()
            
            messages.success(self.request, 'Expense updated successfully.')
            return redirect('finance_management:expense_detail', pk=self.object.pk)
        
        return self.render_to_response(self.get_context_data(form=form))


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'finance_management/expense_confirm_delete.html'
    success_url = reverse_lazy('finance_management:expense_list')
    
    def delete(self, request, *args, **kwargs):
        expense = self.get_object()
        
        # Delete associated journal entry if exists
        if expense.journal_entry:
            expense.journal_entry.delete()
        
        messages.success(request, 'Expense deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ExpenseApprovalView(LoginRequiredMixin, View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        form = ExpenseApprovalForm(request.POST, expense=expense)
        
        if form.is_valid():
            expense.approve_expense(request.user)
            messages.success(request, 'Expense approved successfully.')
        else:
            messages.error(request, 'Error approving expense.')
        
        return redirect('finance_management:expense_detail', pk=pk)


class ExpensePaymentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        form = ExpensePaymentForm(request.POST, expense=expense)
        
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            payment_reference = form.cleaned_data['payment_reference']
            
            expense.mark_as_paid(
                request.user,
                payment_method=payment_method,
                payment_reference=payment_reference
            )
            
            messages.success(request, 'Expense marked as paid successfully.')
        else:
            messages.error(request, 'Error processing payment.')
        
        return redirect('finance_management:expense_detail', pk=pk)


class ExpenseDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/expense_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current period
        current_period = AccountingPeriod.objects.filter(is_current=True).first()
        
        # Expense statistics
        expenses = Expense.objects.all()
        if current_period:
            expenses = expenses.filter(period=current_period)
        
        context['total_expenses'] = expenses.count()
        context['total_amount'] = expenses.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Status breakdown
        status_counts = {}
        for status, _ in Expense.EXPENSE_STATUS_CHOICES:
            status_counts[status] = expenses.filter(status=status).count()
        context['status_counts'] = status_counts
        
        # Category breakdown
        category_totals = expenses.values('expense_category__name').annotate(
            total=Sum('total_amount')
        ).order_by('-total')[:10]
        context['category_totals'] = category_totals
        
        # Recent expenses
        context['recent_expenses'] = expenses.order_by('-created_at')[:5]
        
        # Monthly trend (last 6 months)
        from datetime import datetime, timedelta
        months = []
        amounts = []
        
        for i in range(6):
            date = datetime.now() - timedelta(days=30*i)
            month_expenses = expenses.filter(
                expense_date__year=date.year,
                expense_date__month=date.month
            )
            month_total = month_expenses.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            months.append(date.strftime('%b %Y'))
            amounts.append(float(month_total))
        
        context['monthly_trend'] = {
            'months': months[::-1],
            'amounts': amounts[::-1]
        }
        
        return context

# ============================================================================
# ACCOUNTS PAYABLE VIEWS
# ============================================================================

class AccountsPayableListView(ListView):
    """List view for accounts payable"""
    model = AccountsPayable
    template_name = 'finance_management/accounts_payable_list.html'
    context_object_name = 'payables'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = AccountsPayable.objects.select_related(
            'expense_category', 'period', 'approved_by', 'paid_by'
        ).prefetch_related('line_items')
        
        # Apply filters
        form = AccountsPayableFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            vendor = form.cleaned_data.get('vendor')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            expense_category = form.cleaned_data.get('expense_category')
            
            if search:
                queryset = queryset.filter(
                    Q(vendor__icontains=search) |
                    Q(vendor_invoice_number__icontains=search) |
                    Q(reference_number__icontains=search) |
                    Q(description__icontains=search)
                )
            
            if status:
                queryset = queryset.filter(status=status)
            
            if vendor:
                queryset = queryset.filter(vendor__icontains=vendor)
            
            if date_from:
                queryset = queryset.filter(invoice_date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(invoice_date__lte=date_to)
            
            if expense_category:
                queryset = queryset.filter(expense_category=expense_category)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AccountsPayableFilterForm(self.request.GET)
        
        # Add expense categories for the modal
        context['expense_categories'] = ExpenseCategory.objects.filter(is_active=True)
        
        # Summary statistics
        queryset = self.get_queryset()
        context['total_payables'] = queryset.count()
        context['total_amount'] = queryset.aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        context['total_paid'] = queryset.aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0.00')
        context['total_balance'] = context['total_amount'] - context['total_paid']
        context['overdue_count'] = queryset.filter(status='OVERDUE').count()
        
        return context

class AccountsPayableCreateView(CreateView):
    """Create view for accounts payable"""
    model = AccountsPayable
    form_class = AccountsPayableForm
    template_name = 'finance_management/accounts_payable_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['line_items_formset'] = AccountsPayableLineItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['line_items_formset'] = AccountsPayableLineItemFormSet(
                instance=self.object
            )
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        line_items_formset = context['line_items_formset']
        
        if form.is_valid() and line_items_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            
            # Set period if not specified
            if not self.object.period:
                self.object.period = AccountingPeriod.objects.filter(
                    status='OPEN', is_current=True
                ).first()
            
            self.object.save()
            
            # Save line items
            line_items_formset.instance = self.object
            line_items_formset.save()
            
            # Create journal entry
            self.create_journal_entry()
            
            messages.success(self.request, 'Accounts Payable created successfully!')
            return redirect('finance_management:accounts_payable_list')
        
        return self.render_to_response(self.get_context_data(form=form))
    
    def create_journal_entry(self):
        """Create journal entry for the payable"""
        try:
            # Get accounts payable account
            ap_account = Account.objects.get(code='2000')  # Accounts Payable
            
            # Create journal entry
            journal = Journal.objects.get_or_create(
                journal_type='PURCHASE',
                defaults={'code': 'PUR', 'name': 'Purchase Journal'}
            )[0]
            
            entry = JournalEntry.objects.create(
                journal=journal,
                date=self.object.invoice_date,
                reference=self.object.reference_number,
                description=f"Vendor Invoice: {self.object.vendor}",
                status='POSTED',
                created_by=self.request.user
            )
            
            # Create journal entry lines
            total_debit = Decimal('0.00')
            
            # Debit expense accounts for line items
            for line_item in self.object.line_items.all():
                if line_item.expense_account:
                    expense_account = line_item.expense_account
                else:
                    # Default to general expense account if not specified
                    expense_account = Account.objects.filter(
                        account_type='EXPENSE',
                        status='ACTIVE'
                    ).first()
                
                if expense_account:
                    JournalEntryLine.objects.create(
                        journal_entry=entry,
                        account=expense_account,
                        debit=line_item.line_total,
                        credit=Decimal('0.00'),
                        description=line_item.description
                    )
                    total_debit += line_item.line_total
            
            # Credit accounts payable
            JournalEntryLine.objects.create(
                journal_entry=entry,
                account=ap_account,
                debit=Decimal('0.00'),
                credit=self.object.total_amount,
                description=f"Vendor Invoice: {self.object.vendor}"
            )
            
            # Link journal entry to payable
            self.object.journal_entry = entry
            self.object.save()
            
        except Exception as e:
            # Log error but don't fail the payable creation
            print(f"Error creating journal entry: {e}")

class AccountsPayableDetailView(DetailView):
    """Detail view for accounts payable"""
    model = AccountsPayable
    template_name = 'finance_management/accounts_payable_detail.html'
    context_object_name = 'payable'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['line_items'] = self.object.line_items.all()
        return context

class AccountsPayableUpdateView(UpdateView):
    """Update view for accounts payable"""
    model = AccountsPayable
    form_class = AccountsPayableForm
    template_name = 'finance_management/accounts_payable_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['line_items_formset'] = AccountsPayableLineItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['line_items_formset'] = AccountsPayableLineItemFormSet(
                instance=self.object
            )
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        line_items_formset = context['line_items_formset']
        
        if form.is_valid() and line_items_formset.is_valid():
            self.object = form.save()
            
            # Save line items
            line_items_formset.instance = self.object
            line_items_formset.save()
            
            messages.success(self.request, 'Accounts Payable updated successfully!')
            return redirect('finance_management:accounts_payable_detail', pk=self.object.pk)
        
        return self.render_to_response(self.get_context_data(form=form))

class AccountsPayableDeleteView(DeleteView):
    """Delete view for accounts payable"""
    model = AccountsPayable
    template_name = 'finance_management/accounts_payable_confirm_delete.html'
    success_url = reverse_lazy('finance_management:accounts_payable_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Accounts Payable deleted successfully!')
        return super().delete(request, *args, **kwargs)

class AccountsPayableApprovalView(UpdateView):
    """View for approving accounts payable"""
    model = AccountsPayable
    form_class = AccountsPayableApprovalForm
    template_name = 'finance_management/accounts_payable_approval.html'
    
    def form_valid(self, form):
        if form.cleaned_data['status'] == 'APPROVED':
            self.object.approve(self.request.user)
            messages.success(self.request, 'Accounts Payable approved successfully!')
        else:
            self.object = form.save()
            messages.success(self.request, 'Accounts Payable status updated!')
        
        return redirect('finance_management:accounts_payable_detail', pk=self.object.pk)

class AccountsPayablePaymentView(UpdateView):
    """View for recording payments against accounts payable"""
    model = AccountsPayable
    form_class = AccountsPayablePaymentForm
    template_name = 'finance_management/accounts_payable_payment.html'
    
    def form_valid(self, form):
        payment_amount = form.cleaned_data['payment_amount']
        payment_method = form.cleaned_data['payment_method']
        payment_reference = form.cleaned_data['payment_reference']
        
        # Record payment
        if self.object.record_payment(
            payment_amount, 
            self.request.user, 
            payment_method, 
            payment_reference
        ):
            messages.success(self.request, f'Payment of ${payment_amount} recorded successfully!')
        else:
            messages.error(self.request, 'Failed to record payment!')
        
        return redirect('finance_management:accounts_payable_detail', pk=self.object.pk)

# ============================================================================
# ACCOUNTS RECEIVABLE VIEWS
# ============================================================================

class AccountsReceivableListView(LoginRequiredMixin, TemplateView):
    """List view for accounts receivable (unpaid invoices)"""
    template_name = 'finance_management/accounts_receivable_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get unpaid invoices from the database
        unpaid_invoices = Invoice.objects.filter(
            status__in=['SENT', 'OVERDUE']
        ).select_related('client').order_by('-due_date', '-created_at')
        
        # Handle search functionality
        search_param = self.request.GET.get('search')
        if search_param:
            unpaid_invoices = unpaid_invoices.filter(
                Q(invoice_number__icontains=search_param) |
                Q(client__name__icontains=search_param) |
                Q(description__icontains=search_param)
            )
        
        # Handle status filter
        status_param = self.request.GET.get('status')
        if status_param:
            unpaid_invoices = unpaid_invoices.filter(status=status_param)
        
        # Handle client filter
        client_param = self.request.GET.get('client')
        if client_param:
            unpaid_invoices = unpaid_invoices.filter(client_id=client_param)
        
        # Pagination
        paginator = Paginator(unpaid_invoices, 10)  # Show 10 invoices per page
        page = self.request.GET.get('page')
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Initialize search form
        initial = {}
        if search_param:
            initial['search'] = search_param
        if status_param:
            initial['status'] = status_param
        if client_param:
            initial['client'] = client_param
        
        # Get all clients for the filter dropdown
        clients = Client.objects.filter(is_active=True).order_by('name')
        
        context['unpaid_invoices'] = page_obj
        context['page_obj'] = page_obj
        context['clients'] = clients
        
        # Summary statistics
        context['total_receivables'] = unpaid_invoices.count()
        context['total_amount'] = unpaid_invoices.aggregate(
            total=models.Sum('total')
        )['total'] or Decimal('0.00')
        context['overdue_count'] = unpaid_invoices.filter(status='OVERDUE').count()
        context['overdue_amount'] = unpaid_invoices.filter(status='OVERDUE').aggregate(
            total=models.Sum('total')
        )['total'] or Decimal('0.00')
        
        return context

class AccountsReceivableDetailView(LoginRequiredMixin, DetailView):
    """Detail view for accounts receivable (invoice detail)"""
    model = Invoice
    template_name = 'finance_management/accounts_receivable_detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['line_items'] = self.object.items.all()
        context['payments'] = self.object.payments.all().order_by('-payment_date')
        return context

class AccountsReceivablePaymentView(LoginRequiredMixin, UpdateView):
    """View for recording payments against accounts receivable"""
    model = Invoice
    template_name = 'finance_management/accounts_receivable_payment.html'
    fields = ['status']
    
    def form_valid(self, form):
        # Update invoice status to paid
        self.object.status = 'PAID'
        self.object.save()
        
        messages.success(self.request, 'Payment recorded successfully! Invoice marked as paid.')
        return redirect('finance_management:accounts_receivable_detail', pk=self.object.pk)
