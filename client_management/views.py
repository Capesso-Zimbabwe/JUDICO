from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView
from django.views.generic.list import ListView

from JUDICO_HUB import settings
from .forms import ClientForm, ClientFilterForm, ClientDocumentForm, CaseForm, CaseFilterForm, CaseUpdateForm, CaseDocumentForm
from .models import Client, ClientDocument, Case, CaseUpdate, CaseDocument
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json

# Helper function to check if user is staff
def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def client_list(request):
    # Get all clients
    clients_list = Client.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(clients_list, 10)  # Show 10 clients per page
    page = request.GET.get('page')
    
    try:
        clients = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        clients = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        clients = paginator.page(paginator.num_pages)
    
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


class ClientListView(LoginRequiredMixin, ListView):
    template_name = "client_management/client_list.html"
    paginate_by = settings.PAGINATE_BY
    model = Client
    context_object_name = 'clients'
    ordering = 'name'

    def get_queryset(self):

        queryset = Client.objects.all().order_by('name')

        if search_param := self.request.GET.get('search'):
            queryset = queryset.filter(
                Q(name__icontains=search_param)|
                Q(code__icontains=search_param) |
                Q(contact_person__icontains=search_param)|
                Q(email__icontains=search_param)|
                Q(phone__icontains=search_param)
                )
        return queryset


    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        active_clients = Client.objects.filter(is_active=True).count()
        inactive_clients = Client.objects.filter(is_active=False).count()

        context['active_clients'] = active_clients
        context['inactive_clients'] = inactive_clients
        context['total_clients'] = active_clients + inactive_clients
        initial={}
        if search_param := self.request.GET.get('search'):
            initial['search'] = search_param
        context['search_form'] = ClientFilterForm(initial=initial)
        return context


class ClientDetailsView(LoginRequiredMixin, DetailView):
    template_name = "client_management/client_detail_partial.html"
    model = Client

class ClientCreateView(LoginRequiredMixin, CreateView):
    template_name = "client_management/client_form.html"
    model = Client
    form_class = ClientForm

    def form_valid(self, form):
        client = form.save()
        # Set the user who created the client

        messages.success(self.request, "Client created successfully.")
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse_lazy('client_management:client_list') + f'?search={client.code}'
        return response

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

class ClientUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "client_management/client_form.html"
    model = Client
    form_class = ClientForm
    success_url = reverse_lazy('client_management:client_list')

    def form_valid(self, form):
        client = form.save()
        # Set the user who created the client

        messages.success(self.request, "Client updated successfully.")
        response = HttpResponse(status=204)
        response["HX-Redirect"] = self.get_success_url()+ f'?search={client.name}'
        return response

    def form_invalid(self, form):
        print(form.errors)
        return self.render_to_response(self.get_context_data(form=form, client=self.object))

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

class ClientDocumentCreateView(LoginRequiredMixin, DetailView, CreateView):
    template_name = "client_management/document_form.html"
    model = Client
    form_class = ClientDocumentForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form, client=self.object))


    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form, client=self.object))
    def form_valid(self, form):
        client_document = form.save(commit=False)
        client_document.client = self.object
        client_document.save()
        # Set the user who created the client

        messages.success(self.request, "Client document uploaded successfully.")
        response = HttpResponse(status=204)
        # response["HX-Redirect"] = reverse_lazy('client_management:client_list') + f'?client_id={self.object.id}'
        response["HX-Redirect"] = reverse_lazy('client_management:client_list') + f'?search={self.object.code}'

        return response

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

# Case Management Views

class CaseListView(LoginRequiredMixin, ListView):
    template_name = "client_management/case_list.html"
    paginate_by = settings.PAGINATE_BY
    model = Case
    context_object_name = 'cases'
    ordering = '-created_date'

    def get_queryset(self):
        queryset = Case.objects.select_related('client', 'assigned_lawyer', 'lawyer').order_by('-created_date')

        if search_param := self.request.GET.get('search'):
            queryset = queryset.filter(
                Q(title__icontains=search_param) |
                Q(code__icontains=search_param) |
                Q(client__name__icontains=search_param) |
                Q(description__icontains=search_param)
            )
        
        if status_param := self.request.GET.get('status'):
            queryset = queryset.filter(status=status_param)
        
        if priority_param := self.request.GET.get('priority'):
            queryset = queryset.filter(priority=priority_param)
        
        if case_type_param := self.request.GET.get('case_type'):
            queryset = queryset.filter(case_type=case_type_param)
        
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        
        # Case statistics
        pending_cases = Case.objects.filter(status='pending').count()
        active_cases = Case.objects.filter(status='active').count()
        completed_cases = Case.objects.filter(status='completed').count()
        overdue_cases = Case.objects.filter(
            expected_completion_date__lt=timezone.now().date(),
            status__in=['pending', 'active', 'on_hold']
        ).count()
        
        context.update({
            'pending_cases': pending_cases,
            'active_cases': active_cases,
            'completed_cases': completed_cases,
            'overdue_cases': overdue_cases,
            'total_cases': pending_cases + active_cases + completed_cases
        })
        
        # Filter form
        initial = {}
        for param in ['search', 'status', 'priority', 'case_type']:
            if value := self.request.GET.get(param):
                initial[param] = value
        context['filter_form'] = CaseFilterForm(initial=initial)
        
        return context

class CaseDetailsView(LoginRequiredMixin, DetailView):
    template_name = "client_management/case_detail_partial.html"
    model = Case
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['case'] = self.object  # Explicitly set case context variable
        context['case_updates'] = self.object.updates.all()[:10]
        context['case_documents'] = self.object.documents.all()
        return context

class CaseCreateView(LoginRequiredMixin, CreateView):
    template_name = "client_management/case_form.html"
    model = Case
    form_class = CaseForm

    def form_valid(self, form):
        case = form.save(commit=False)
        case.created_by = self.request.user
        case.save()
        
        messages.success(self.request, "Case created successfully.")
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse_lazy('client_management:case_list') + f'?search={case.code}'
        return response

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

class CaseUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "client_management/case_form.html"
    model = Case
    form_class = CaseForm
    success_url = reverse_lazy('client_management:case_list')

    def form_valid(self, form):
        case = form.save()
        
        messages.success(self.request, "Case updated successfully.")
        response = HttpResponse(status=204)
        response["HX-Redirect"] = self.get_success_url() + f'?search={case.code}'
        return response

    def form_invalid(self, form):
        print(form.errors)
        return self.render_to_response(self.get_context_data(form=form, case=self.object))

@login_required
@user_passes_test(is_staff)
def case_delete(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        case.delete()
        return redirect('client_management:case_list')
    
    return render(request, 'client_management/case_confirm_delete.html', {'case': case})

@login_required
@user_passes_test(is_staff)
def case_dashboard(request):
    from django.utils import timezone
    
    # Get case counts
    total_cases = Case.objects.count()
    pending_cases = Case.objects.filter(status='pending').count()
    active_cases = Case.objects.filter(status='active').count()
    completed_cases = Case.objects.filter(status='completed').count()
    overdue_cases = Case.objects.filter(
        expected_completion_date__lt=timezone.now().date(),
        status__in=['pending', 'active', 'on_hold']
    ).count()
    
    # Get top lawyers by assigned cases
    top_lawyers = User.objects.filter(groups__name='Lawyers').annotate(
        case_count=Count('assigned_cases')
    ).order_by('-case_count')[:5]
    
    lawyer_labels = json.dumps([lawyer.get_full_name() or lawyer.username for lawyer in top_lawyers])
    lawyer_cases_data = json.dumps([lawyer.case_count for lawyer in top_lawyers])
    
    # Get recent cases
    recent_cases = Case.objects.select_related('client').order_by('-created_date')[:10]
    
    # Get case status distribution
    status_data = []
    status_labels = []
    for status_code, status_name in Case.STATUS_CHOICES:
        count = Case.objects.filter(status=status_code).count()
        if count > 0:
            status_data.append(count)
            status_labels.append(status_name)
    
    context = {
        'total_cases': total_cases,
        'pending_cases': pending_cases,
        'active_cases': active_cases,
        'completed_cases': completed_cases,
        'overdue_cases': overdue_cases,
        'lawyer_labels': lawyer_labels,
        'lawyer_cases_data': lawyer_cases_data,
        'recent_cases': recent_cases,
        'status_data': json.dumps(status_data),
        'status_labels': json.dumps(status_labels),
    }
    
    return render(request, 'client_management/case_dashboard.html', context)

# Case Update Views

class CaseUpdateCreateView(LoginRequiredMixin, DetailView, CreateView):
    template_name = "client_management/case_update_form.html"
    model = Case
    form_class = CaseUpdateForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form, case=self.object))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form, case=self.object))
    
    def form_valid(self, form):
        case_update = form.save(commit=False)
        case_update.case = self.object
        case_update.created_by = self.request.user
        case_update.save()
        
        messages.success(self.request, "Case update added successfully.")
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse_lazy('client_management:case_list') + f'?search={self.object.code}'
        return response

# Case Document Views

class CaseDocumentCreateView(LoginRequiredMixin, DetailView, CreateView):
    template_name = "client_management/case_document_form.html"
    model = Case
    form_class = CaseDocumentForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form, case=self.object))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form, case=self.object))
    
    def form_valid(self, form):
        case_document = form.save(commit=False)
        case_document.case = self.object
        case_document.uploaded_by = self.request.user
        case_document.save()
        
        messages.success(self.request, "Case document uploaded successfully.")
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse_lazy('client_management:case_list') + f'?search={self.object.code}'
        return response

@login_required
@user_passes_test(is_staff)
def delete_case_document(request, document_id):
    document = get_object_or_404(CaseDocument, id=document_id)
    case_id = document.case.id
    
    if request.method == 'POST':
        document.delete()
        return redirect('client_management:case_detail', case_id=case_id)
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        document.delete()
        return JsonResponse({'success': True})
    
    return redirect('client_management:case_detail', case_id=case_id)
