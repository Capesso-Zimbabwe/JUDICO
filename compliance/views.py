from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def compliance_dashboard(request):
    context = {
        'total_requirements': 0,
        'total_audits': 0,
        'total_reports': 0,
    }
    return render(request, 'compliance/dashboard.html', context)

@login_required
def requirements_list(request):
    return render(request, 'compliance/requirements.html')

@login_required
def audits_list(request):
    return render(request, 'compliance/audits.html')

@login_required
def compliance_reports(request):
    return render(request, 'compliance/reports.html')

# Create your views here.
