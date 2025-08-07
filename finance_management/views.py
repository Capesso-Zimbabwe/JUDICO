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
from decimal import Decimal
import json
from .models import Invoice, InvoiceItem, Payment, Expense, Account, JournalEntry, JournalEntryLine, PettyCash, Report
from .forms import InvoiceForm, PaymentForm, ExpenseForm, ExpenseFilterForm, AccountForm, AccountFilterForm, JournalEntryForm, JournalEntryFilterForm, JournalEntryLineFormSet, InvoiceFilterForm, PettyCashForm, PettyCashFilterForm, ReportForm, ReportFilterForm
from client_management.models import Client

class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_management/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get summary statistics
        total_revenue = Invoice.objects.filter(status='PAID').aggregate(total=Sum('total'))['total'] or 0
        total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
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
            monthly_expenses[month_index] += float(expense.amount)
        
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
            total = Expense.objects.filter(category=category_key).aggregate(total=Sum('amount'))['total'] or 0
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
            
            if report.status != 'completed' or not report.file_path:
                messages.error(request, 'Report is not ready for download.')
                return JsonResponse({'error': 'Report not ready'}, status=400)
            
            # For now, just return a success message
            # In a real implementation, you would serve the actual file
            messages.success(request, f'Report "{report.name}" download started.')
            return JsonResponse({'success': True, 'message': 'Download started'})
            
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)

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
