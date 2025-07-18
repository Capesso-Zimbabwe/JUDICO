from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Client, ClientDocument
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import JsonResponse
import json

# Helper function to check if user is staff
def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def client_list(request):
    # Get all clients
    clients = Client.objects.all().order_by('name')
    
    # Get active and inactive client counts
    active_clients = Client.objects.filter(is_active=True).count()
    inactive_clients = Client.objects.filter(is_active=False).count()
    
    context = {
        'clients': clients,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'total_clients': active_clients + inactive_clients
    }
    
    return render(request, 'client_management/client_list.html', context)

@login_required
@user_passes_test(is_staff)
def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    documents = client.documents.all().order_by('-uploaded_at')
    
    context = {
        'client': client,
        'documents': documents
    }
    
    return render(request, 'client_management/client_detail.html', context)

@login_required
@user_passes_test(is_staff)
def client_create(request):
    if request.method == 'POST':
        # Process form data
        name = request.POST.get('name')
        contact_person = request.POST.get('contact_person')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        assigned_lawyer_id = request.POST.get('assigned_lawyer')
        
        # Create new client
        client = Client(
            name=name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            address=address
        )
        
        if assigned_lawyer_id:
            client.assigned_lawyer_id = assigned_lawyer_id
            
        client.save()
        
        return redirect('client_management:client_detail', client_id=client.id)
    
    # Get lawyers for form
    lawyers = User.objects.filter(groups__name='Lawyers')
    
    context = {
        'lawyers': lawyers
    }
    
    return render(request, 'client_management/client_form.html', context)

@login_required
@user_passes_test(is_staff)
def client_update(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        # Process form data
        client.name = request.POST.get('name')
        client.contact_person = request.POST.get('contact_person')
        client.email = request.POST.get('email')
        client.phone = request.POST.get('phone')
        client.address = request.POST.get('address')
        client.is_active = request.POST.get('is_active') == 'on'
        assigned_lawyer_id = request.POST.get('assigned_lawyer')
        
        if assigned_lawyer_id:
            client.assigned_lawyer_id = assigned_lawyer_id
        else:
            client.assigned_lawyer = None
            
        client.save()
        
        return redirect('client_management:client_detail', client_id=client.id)
    
    # Get lawyers for form
    lawyers = User.objects.filter(groups__name='Lawyers')
    
    context = {
        'client': client,
        'lawyers': lawyers
    }
    
    return render(request, 'client_management/client_form.html', context)

@login_required
@user_passes_test(is_staff)
def client_delete(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        client.delete()
        return redirect('client_management:client_list')
    
    return render(request, 'client_management/client_confirm_delete.html', {'client': client})

@login_required
@user_passes_test(is_staff)
def client_dashboard(request):
    # Get client counts
    total_clients = Client.objects.count()
    active_clients = Client.objects.filter(is_active=True).count()
    inactive_clients = Client.objects.filter(is_active=False).count()
    
    # Get top lawyers by assigned clients
    top_lawyers = User.objects.filter(groups__name='Lawyers').annotate(
        client_count=Count('assigned_clients')
    ).order_by('-client_count')[:5]
    
    lawyer_labels = json.dumps([lawyer.get_full_name() or lawyer.username for lawyer in top_lawyers])
    lawyer_clients_data = json.dumps([lawyer.client_count for lawyer in top_lawyers])
    
    # Get recent clients
    recent_clients = Client.objects.all().order_by('-registration_date')[:10]
    
    # Get document counts
    total_documents = ClientDocument.objects.count()
    
    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'lawyer_labels': lawyer_labels,
        'lawyer_clients_data': lawyer_clients_data,
        'recent_clients': recent_clients,
        'total_documents': total_documents
    }
    
    return render(request, 'client_management/client_dashboard.html', context)

@login_required
@user_passes_test(is_staff)
def upload_document(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST' and request.FILES.get('document'):
        title = request.POST.get('title')
        document = request.FILES.get('document')
        
        # Create new document
        client_document = ClientDocument(
            client=client,
            title=title,
            document=document
        )
        client_document.save()
        
        return redirect('client_management:client_detail', client_id=client.id)
    
    return redirect('client_management:client_detail', client_id=client.id)

@login_required
@user_passes_test(is_staff)
def delete_document(request, document_id):
    document = get_object_or_404(ClientDocument, id=document_id)
    client_id = document.client.id
    
    if request.method == 'POST':
        document.delete()
        return redirect('client_management:client_detail', client_id=client_id)
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        document.delete()
        return JsonResponse({'success': True})
    
    return redirect('client_management:client_detail', client_id=client_id)
