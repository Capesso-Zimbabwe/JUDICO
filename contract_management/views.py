from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import base64
from io import BytesIO
from PIL import Image

from .models import Contract, ContractSignature, ContractTemplate, ContractAmendment
from .forms import (
    ContractForm, ContractSignatureForm, ContractTemplateForm, 
    ContractAmendmentForm, ContractFilterForm, SignatureForm
)
from client_management.models import Client

# Helper function to check if user is staff, lawyer, or client
def is_staff_or_lawyer_or_client(user):
    return user.is_staff or hasattr(user, 'lawyer_profile') or hasattr(user, 'client_profile')

# Dashboard view
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def contract_dashboard(request):
    # Get contract statistics
    total_contracts = Contract.objects.count()
    active_contracts = Contract.objects.filter(status__in=['signed', 'executed']).count()
    pending_contracts = Contract.objects.filter(status='pending_signature').count()
    draft_contracts = Contract.objects.filter(status='draft').count()
    
    # Get contracts by type
    contracts_by_type = Contract.objects.values('contract_type').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Get recent contracts
    recent_contracts = Contract.objects.select_related('client', 'assigned_lawyer').order_by('-created_at')[:10]
    
    # Get contracts expiring soon (within 30 days)
    from datetime import datetime, timedelta
    thirty_days_from_now = datetime.now().date() + timedelta(days=30)
    expiring_contracts = Contract.objects.filter(
        end_date__lte=thirty_days_from_now,
        end_date__gte=datetime.now().date(),
        status__in=['signed', 'executed']
    ).count()
    
    # Get pending signatures
    pending_signatures = ContractSignature.objects.filter(status='pending').count()
    
    context = {
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'pending_contracts': pending_contracts,
        'draft_contracts': draft_contracts,
        'contracts_by_type': contracts_by_type,
        'recent_contracts': recent_contracts,
        'expiring_contracts': expiring_contracts,
        'pending_signatures': pending_signatures,
    }
    
    return render(request, 'contract_management/dashboard.html', context)

# Contract list view
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def contract_list(request):
    contracts = Contract.objects.select_related('client', 'assigned_lawyer', 'created_by').order_by('-created_at')
    
    # Apply filters
    filter_form = ContractFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data['status']:
            contracts = contracts.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['contract_type']:
            contracts = contracts.filter(contract_type=filter_form.cleaned_data['contract_type'])
        if filter_form.cleaned_data['client']:
            contracts = contracts.filter(client=filter_form.cleaned_data['client'])
        if filter_form.cleaned_data['assigned_lawyer']:
            contracts = contracts.filter(assigned_lawyer=filter_form.cleaned_data['assigned_lawyer'])
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        contracts = contracts.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(client__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(contracts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'search_query': search_query,
    }
    
    return render(request, 'contract_management/contract_list.html', context)

# Contract detail view
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def contract_detail(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related('client', 'assigned_lawyer', 'created_by'),
        pk=pk
    )
    
    signatures = contract.signatures.all().order_by('-created_at')
    amendments = contract.amendments.all().order_by('-created_at')
    
    context = {
        'contract': contract,
        'signatures': signatures,
        'amendments': amendments,
    }
    
    return render(request, 'contract_management/contract_detail.html', context)

# Contract create view
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def contract_create(request):
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.created_by = request.user
            contract.save()
            messages.success(request, 'Contract created successfully!')
            return redirect('contract_management:contract_detail', pk=contract.pk)
    else:
        form = ContractForm()
    
    context = {
        'form': form,
        'title': 'Create New Contract'
    }
    
    return render(request, 'contract_management/contract_form.html', context)

# Contract update view
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def contract_update(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contract updated successfully!')
            return redirect('contract_management:contract_detail', pk=contract.pk)
    else:
        form = ContractForm(instance=contract)
    
    context = {
        'form': form,
        'contract': contract,
        'title': 'Update Contract'
    }
    
    return render(request, 'contract_management/contract_form.html', context)

# Contract delete view
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        contract.delete()
        messages.success(request, 'Contract deleted successfully!')
        return redirect('contract_management:contract_list')
    
    context = {
        'contract': contract
    }
    
    return render(request, 'contract_management/contract_confirm_delete.html', context)

# Signature management views
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def add_signature_request(request, contract_pk):
    contract = get_object_or_404(Contract, pk=contract_pk)
    
    if request.method == 'POST':
        form = ContractSignatureForm(request.POST)
        if form.is_valid():
            signature = form.save(commit=False)
            signature.contract = contract
            signature.save()
            messages.success(request, 'Signature request added successfully!')
            return redirect('contract_management:contract_detail', pk=contract.pk)
    else:
        form = ContractSignatureForm()
    
    context = {
        'form': form,
        'contract': contract,
        'title': 'Add Signature Request'
    }
    
    return render(request, 'contract_management/signature_form.html', context)

# Digital signature view (for clients/signers)
def contract_sign(request, signature_id, verification_code):
    signature = get_object_or_404(
        ContractSignature,
        id=signature_id,
        verification_code=verification_code,
        status='pending'
    )
    
    if request.method == 'POST':
        form = SignatureForm(request.POST)
        if form.is_valid():
            # Process the signature
            signature_data = form.cleaned_data['signature_data']
            
            # Save signature image
            if signature_data:
                # Decode base64 signature data
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]
                
                # Create image file
                image_data = base64.b64decode(imgstr)
                image = Image.open(BytesIO(image_data))
                
                # Save signature
                signature.status = 'signed'
                signature.signed_at = timezone.now()
                signature.ip_address = request.META.get('REMOTE_ADDR')
                signature.user_agent = request.META.get('HTTP_USER_AGENT', '')
                signature.is_verified = True
                
                # Save signature image (you might want to implement proper file handling)
                signature.save()
                
                # Check if all required signatures are complete
                contract = signature.contract
                required_signatures = contract.signatures.filter(status='pending')
                if not required_signatures.exists():
                    contract.status = 'signed'
                    contract.signed_at = timezone.now()
                    contract.save()
                
                return render(request, 'contract_management/signature_success.html', {
                    'signature': signature,
                    'contract': contract
                })
    else:
        form = SignatureForm()
    
    context = {
        'signature': signature,
        'contract': signature.contract,
        'form': form
    }
    
    return render(request, 'contract_management/contract_sign.html', context)

# Template management views
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def template_list(request):
    templates = ContractTemplate.objects.filter(is_active=True).order_by('name')
    
    context = {
        'templates': templates
    }
    
    return render(request, 'contract_management/template_list.html', context)

@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def template_create(request):
    if request.method == 'POST':
        form = ContractTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Template created successfully!')
            return redirect('contract_management:template_list')
    else:
        form = ContractTemplateForm()
    
    context = {
        'form': form,
        'title': 'Create Contract Template'
    }
    
    return render(request, 'contract_management/template_form.html', context)

# Amendment management
@login_required
@user_passes_test(is_staff_or_lawyer_or_client)
def add_amendment(request, contract_pk):
    contract = get_object_or_404(Contract, pk=contract_pk)
    
    if request.method == 'POST':
        form = ContractAmendmentForm(request.POST, request.FILES)
        if form.is_valid():
            amendment = form.save(commit=False)
            amendment.contract = contract
            amendment.created_by = request.user
            amendment.save()
            messages.success(request, 'Amendment added successfully!')
            return redirect('contract_management:contract_detail', pk=contract.pk)
    else:
        form = ContractAmendmentForm()
    
    context = {
        'form': form,
        'contract': contract,
        'title': 'Add Contract Amendment'
    }
    
    return render(request, 'contract_management/amendment_form.html', context)

# API endpoints for AJAX requests
@login_required
@require_POST
def update_contract_status(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(Contract.CONTRACT_STATUS_CHOICES).keys():
        contract.status = new_status
        if new_status == 'signed':
            contract.signed_at = timezone.now()
        contract.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Contract status updated successfully!'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid status provided.'
    })

@login_required
def contract_statistics(request):
    """API endpoint for contract statistics"""
    stats = {
        'total_contracts': Contract.objects.count(),
        'by_status': {},
        'by_type': {},
        'monthly_created': []
    }
    
    # Contracts by status
    for status_code, status_name in Contract.CONTRACT_STATUS_CHOICES:
        stats['by_status'][status_name] = Contract.objects.filter(status=status_code).count()
    
    # Contracts by type
    for type_code, type_name in Contract.CONTRACT_TYPE_CHOICES:
        stats['by_type'][type_name] = Contract.objects.filter(contract_type=type_code).count()
    
    return JsonResponse(stats)
