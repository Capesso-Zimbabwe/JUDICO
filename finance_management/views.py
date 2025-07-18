from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
import json
from datetime import datetime, timedelta
from .models import Invoice, InvoiceItem, Payment, Expense
from .forms import InvoiceForm, InvoiceItemForm, PaymentForm, ExpenseForm

@login_required
def finance_dashboard(request):
    # Get summary statistics
    total_invoices = Invoice.objects.aggregate(total=Sum('total'))['total'] or 0
    paid_invoices = Invoice.objects.filter(status='PAID').aggregate(total=Sum('total'))['total'] or 0
    overdue_invoices = Invoice.objects.filter(status='OVERDUE').aggregate(total=Sum('total'))['total'] or 0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get invoice counts by status
    paid_count = Invoice.objects.filter(status='PAID').count()
    overdue_count = Invoice.objects.filter(status='OVERDUE').count()
    sent_count = Invoice.objects.filter(status='SENT').count()
    draft_count = Invoice.objects.filter(status='DRAFT').count()
    
    # Get recent payments
    recent_payments = Payment.objects.order_by('-payment_date')[:5]
    
    # Get recent expenses
    recent_expenses = Expense.objects.order_by('-expense_date')[:5]
    
    # Get recent invoices
    recent_invoices = Invoice.objects.order_by('-issue_date')[:10]
    
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
    
    context = {
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'overdue_invoices': overdue_invoices,
        'total_expenses': total_expenses,
        'paid_count': paid_count,
        'overdue_count': overdue_count,
        'sent_count': sent_count,
        'draft_count': draft_count,
        'recent_payments': recent_payments,
        'recent_expenses': recent_expenses,
        'recent_invoices': recent_invoices,
        'monthly_revenue': json.dumps(monthly_revenue),
        'monthly_expenses': json.dumps(monthly_expenses),
        'expense_categories': json.dumps(expense_categories)
    }
    return render(request, 'finance_management/dashboard.html', context)

@login_required
def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-issue_date')
    return render(request, 'finance_management/invoice_list.html', {'invoices': invoices})

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    payments = invoice.payments.all()
    return render(request, 'finance_management/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'payments': payments
    })

@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            messages.success(request, 'Invoice created successfully.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()
    return render(request, 'finance_management/invoice_form.html', {'form': form})

@login_required
def payment_list(request):
    payments = Payment.objects.all().order_by('-payment_date')
    return render(request, 'finance_management/payment_list.html', {'payments': payments})

@login_required
def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('payment_list')
    else:
        form = PaymentForm()
    return render(request, 'finance_management/payment_form.html', {'form': form})

@login_required
def expense_list(request):
    expenses = Expense.objects.all().order_by('-expense_date')
    return render(request, 'finance_management/expense_list.html', {'expenses': expenses})

@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    return render(request, 'finance_management/expense_detail.html', {'expense': expense})

@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'Expense recorded successfully.')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'finance_management/expense_form.html', {'form': form})
