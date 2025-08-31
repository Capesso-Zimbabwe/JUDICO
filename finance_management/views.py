from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import JsonResponse, HttpResponse
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
        
        # Get summary statistics
        total_revenue = Invoice.objects.filter(status='PAID').aggregate(total=Sum('total'))['total'] or 0
        total_expenses = Expense.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        
        context['total_revenue'] = total_revenue
        context['total_expenses'] = total_expenses
        context['net_profit'] = total_revenue - total_expenses
        context['pending_invoices'] = Invoice.objects.filter(status__in=['SENT', 'OVERDUE']).count()
        
        # Get invoice counts by status
        context['paid_count'] = Invoice.objects.filter(status='PAID').count()
        context['overdue_count'] = Invoice.objects.filter(status='OVERDUE').count()
        context['sent_count'] = Invoice.objects.filter(status='SENT').count()
        context['draft_count'] = Invoice.objects.filter(status='DRAFT').count()
        
        # Get recent payments
        context['recent_payments'] = Payment.objects.select_related('invoice__client').order_by('-payment_date')[:5]
        
        # Get recent expenses
        context['recent_expenses'] = Expense.objects.order_by('-expense_date')[:5]
        
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
        category_mapping = {
            'OFFICE_SUPPLIES': 'Office Supplies',
            'UTILITIES': 'Utilities',
            'RENT': 'Rent',
            'TRAVEL': 'Travel',
            'PROFESSIONAL_FEES': 'Professional Fees',
            'MARKETING': 'Marketing',
            'OTHER': 'Other'
        }
        
        for category_key, category_label in category_mapping.items():
            total = Expense.objects.filter(expense_category__name=category_key).aggregate(total=Sum('total_amount'))['total'] or 0
            if total > 0:
                expense_categories_data.append(float(total))
                expense_categories_labels.append(category_label)
        
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
        
        # Financial metrics
        context['collection_rate'] = 92  # Default value
        context['avg_payment_time'] = 15  # Default value
        context['outstanding_amount'] = Invoice.objects.filter(status__in=['SENT', 'OVERDUE']).aggregate(total=Sum('total'))['total'] or 0
        context['monthly_growth'] = '+8.5'  # Default value
        context['finance_status'] = 'All financial reports up to date'
        
        # Convert data to JSON for charts
        context['monthly_revenue'] = json.dumps(monthly_revenue)
        context['monthly_expenses'] = json.dumps(monthly_expenses)
        context['monthly_labels'] = json.dumps(monthly_labels)
        context['expense_categories_data'] = json.dumps(expense_categories_data)
        context['expense_categories_labels'] = json.dumps(expense_categories_labels)
        context['invoice_status_data'] = json.dumps(invoice_status_data)
        context['client_revenue_labels'] = json.dumps(client_revenue_labels)
        context['client_revenue_data'] = json.dumps(client_revenue_data)
        
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
        queryset = Invoice.objects.all().order_by('-issue_date')
        
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
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create a simple search form context
        search_param = self.request.GET.get('search')
        context['search_form'] = {'search': search_param or ''}
        
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

class ReportListView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get reports from the database
        reports = Report.objects.all().order_by('-created_at')
        
        # Handle search functionality
        search_param = self.request.GET.get('search')
        if search_param:
            reports = reports.filter(
                Q(name__icontains=search_param) |
                Q(report_type__icontains=search_param) |
                Q(description__icontains=search_param)
            )
        
        # Handle report type filter
        report_type_param = self.request.GET.get('report_type')
        if report_type_param:
            reports = reports.filter(report_type=report_type_param)
        
        # Pagination
        paginator = Paginator(reports, 10)  # Show 10 reports per page
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
        if report_type_param:
            initial['report_type'] = report_type_param
        search_form = ReportFilterForm(initial=initial)
        
        context['reports'] = page_obj
        context['page_obj'] = page_obj
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
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:reports')
            return response
        
        return render(request, 'finance_management/modals/report_form.html', {
            'form': form,
            'modal_id': 'new-report-modal'
        })

class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'finance_management/report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
