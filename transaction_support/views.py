from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def transaction_dashboard(request):
    return render(request, 'transaction_support/dashboard.html')

@login_required
def transaction_list(request):
    return render(request, 'transaction_support/transaction_list.html')

@login_required
def transaction_create(request):
    return render(request, 'transaction_support/transaction_form.html')

@login_required
def transaction_monitoring(request):
    return render(request, 'transaction_support/monitoring.html')

@login_required
def transaction_reports(request):
    return render(request, 'transaction_support/reports.html')

# Create your views here.
