from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
from .models import Invoice, InvoiceItem, Payment, Expense, Account, JournalEntry, JournalEntryLine
from .forms import InvoiceForm, PaymentForm, ExpenseForm, ExpenseFilterForm, AccountForm, AccountFilterForm, JournalEntryForm, JournalEntryFilterForm, JournalEntryLineFormSet

class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get summary statistics
        context['total_invoices'] = Invoice.objects.aggregate(total=Sum('total'))['total'] or 0
        context['paid_invoices'] = Invoice.objects.filter(status='PAID').aggregate(total=Sum('total'))['total'] or 0
        context['overdue_invoices'] = Invoice.objects.filter(status='OVERDUE').aggregate(total=Sum('total'))['total'] or 0
        context['total_expenses'] = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get invoice counts by status
        context['paid_count'] = Invoice.objects.filter(status='PAID').count()
        context['overdue_count'] = Invoice.objects.filter(status='OVERDUE').count()
        context['sent_count'] = Invoice.objects.filter(status='SENT').count()
        context['draft_count'] = Invoice.objects.filter(status='DRAFT').count()
        
        # Get recent payments
        context['recent_payments'] = Payment.objects.order_by('-payment_date')[:5]
        
        # Get recent expenses
        context['recent_expenses'] = Expense.objects.order_by('-expense_date')[:5]
        
        # Get recent invoices
        context['recent_invoices'] = Invoice.objects.order_by('-issue_date')[:10]
        
        # Calculate monthly revenue and expenses for the current year
        current_year = timezone.now().year
        monthly_revenue = [0] * 12
        monthly_expenses = [0] * 12
        
        # Get monthly revenue from payments
        payments = Payment.objects.filter(payment_date__year=current_year)
        for payment in payments:
            month_index = payment.payment_date.month - 1  # 0-based index
            monthly_revenue[month_index] += float(payment.amount)
        
        # Get monthly expenses
        expenses = Expense.objects.filter(expense_date__year=current_year)
        for expense in expenses:
            month_index = expense.expense_date.month - 1  # 0-based index
            monthly_expenses[month_index] += float(expense.amount)
        
        # Get expense categories distribution
        expense_categories = [0] * 7  # 7 categories as defined in the model
        category_mapping = {
            'OFFICE_SUPPLIES': 0,
            'UTILITIES': 1,
            'RENT': 2,
            'TRAVEL': 3,
            'PROFESSIONAL_FEES': 4,
            'MARKETING': 5,
            'OTHER': 6
        }
        
        for expense in Expense.objects.all():
            category_index = category_mapping.get(expense.category, 6)  # Default to 'OTHER' if not found
            expense_categories[category_index] += float(expense.amount)
        
        context['monthly_revenue'] = json.dumps(monthly_revenue)
        context['monthly_expenses'] = json.dumps(monthly_expenses)
        context['expense_categories'] = json.dumps(expense_categories)
        
        return context

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'finance_management/invoice_list.html'
    context_object_name = 'invoices'
    ordering = ['-issue_date']

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'finance_management/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        return context

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance_management/invoice_form.html'
    
    def get_success_url(self):
        return reverse_lazy('invoice_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Invoice created successfully.')
        return super().form_valid(form)

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
        if search_param:
            accounts = accounts.filter(
                Q(name__icontains=search_param) |
                Q(code__icontains=search_param) |
                Q(account_type__icontains=search_param)
            )
        
        # Pagination
        paginator = Paginator(accounts, 10)  # Show 10 accounts per page
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
        search_form = AccountFilterForm(initial=initial)
        
        context['accounts'] = page_obj
        context['page_obj'] = page_obj
        context['search_form'] = search_form
        
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

class JournalEntryCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = JournalEntryForm()
        formset = JournalEntryLineFormSet()
        
        # Check if this is an HTMX request for modal content
        if request.headers.get('HX-Request'):
            # Return only the modal content for HTMX requests
            return render(request, 'finance_management/modals/new_journal_entry_modal.html', {
                'form': form,
                'formset': formset,
                'modal_id': 'new-modal',
                'accounts': Account.objects.filter(status='ACTIVE').order_by('code')
            })
        
        # Return full page for regular requests
        return render(request, 'finance_management/journal_entry_form.html', {
            'form': form,
            'formset': formset
        })
    
    def post(self, request):
        form = JournalEntryForm(request.POST)
        formset = JournalEntryLineFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.created_by = request.user
            
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
            
            messages.success(request, 'Journal entry created successfully.')
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse_lazy('finance_management:journal_entries')
            return response
        
        # Handle form errors
        if request.headers.get('HX-Request'):
            # Return modal content with errors for HTMX requests
            return render(request, 'finance_management/modals/new_journal_entry_modal.html', {
                'form': form,
                'formset': formset,
                'modal_id': 'new-modal',
                'accounts': Account.objects.filter(status='ACTIVE').order_by('code')
            })
        
        # Return full page with errors for regular requests
        return render(request, 'finance_management/journal_entry_form.html', {
            'form': form,
            'formset': formset
        })

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
    template_name = 'finance_management/journal_entry_update.html'
    
    def get_success_url(self):
        return reverse_lazy('finance_management:journal_entries')
    
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
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

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
            return render(self.request, self.template_name, {'form': form, 'expense': self.object})
        
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
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class ExpenseDetailAPIView(LoginRequiredMixin, View):
    """API view to return expense details as JSON for modal population"""
    
    def get(self, request, pk):
        try:
            expense = get_object_or_404(Expense, pk=pk)
            data = {
                'id': expense.id,
                'title': expense.title,
                'description': expense.description,
                'amount': str(expense.amount),
                'category': expense.category,
                'category_display': expense.get_category_display(),
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
