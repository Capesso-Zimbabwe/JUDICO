from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import datetime, date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView
from django.views.generic.list import ListView

from JUDICO_HUB import settings
from .forms import ClientForm, ClientFilterForm, ClientDocumentForm, CaseForm, CaseFilterForm, CaseUpdateForm, CaseDocumentForm, CourtDateForm
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
        
        # Create an initial case for the new client
        Case.objects.create(
            client=client,
            title=f"Initial Consultation - {client.name}",
            description=f"Initial case consultation and legal assessment for {client.name}.",
            case_type=client.case_type,
            status='pending',
            priority='medium',
            created_by=self.request.user
        )

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
    from django.db.models import Avg
    
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
    
    # Additional data for summary sections
    current_date = timezone.now().date()
    current_month_start = current_date.replace(day=1)
    
    # Recent client activities (using client registration and document uploads)
    recent_client_activities = []
    
    # Add recent client registrations
    week_ago = timezone.now() - timedelta(days=7)
    recent_registrations = Client.objects.filter(
        registration_date__gte=week_ago
    ).order_by('-registration_date')[:3]
    
    for client in recent_registrations:
        # Convert date to datetime for consistent sorting
        if isinstance(client.registration_date, date) and not isinstance(client.registration_date, datetime):
            created_at = timezone.make_aware(datetime.combine(client.registration_date, datetime.min.time()))
        else:
            created_at = client.registration_date
        
        recent_client_activities.append({
            'description': f'New client "{client.name}" added',
            'created_at': created_at,
            'color': 'green'
        })
    
    # Add recent document uploads
    recent_documents = ClientDocument.objects.filter(
        uploaded_at__gte=week_ago
    ).select_related('client').order_by('-uploaded_at')[:3]
    
    for doc in recent_documents:
        recent_client_activities.append({
            'description': f'Document uploaded for "{doc.client.name}"',
            'created_at': doc.uploaded_at,
            'color': 'blue'
        })
    
    # Sort activities by date (now all datetime objects)
    recent_client_activities.sort(key=lambda x: x['created_at'], reverse=True)
    recent_client_activities = recent_client_activities[:4]
    
    # Upcoming client tasks (using cases as tasks)
    thirty_days_ahead = current_date + timedelta(days=30)
    upcoming_client_tasks = Case.objects.filter(
        status__in=['pending', 'active'],
        expected_completion_date__gte=current_date,
        expected_completion_date__lte=thirty_days_ahead
    ).select_related('client').order_by('expected_completion_date')[:3]
    
    # Format tasks for template
    formatted_tasks = []
    for case in upcoming_client_tasks:
        priority_color = {
            'high': 'red',
            'medium': 'yellow',
            'low': 'green'
        }.get(case.priority, 'gray')
        
        formatted_tasks.append({
            'title': case.title,
            'client_name': case.client.name,
            'due_date': case.expected_completion_date,
            'priority': case.priority.title(),
            'priority_color': priority_color
        })
    
    # Client retention rate (percentage of active clients)
    client_retention_rate = round((active_clients / total_clients * 100) if total_clients > 0 else 0)
    
    # Average response time (mock data - you can implement actual tracking)
    avg_response_time = "2.3 hours"
    
    # Documents processed this month
    month_start_datetime = timezone.make_aware(datetime.combine(current_month_start, datetime.min.time()))
    documents_this_month = ClientDocument.objects.filter(
        uploaded_at__gte=month_start_datetime
    ).count()
    
    # New clients this month
    new_clients_this_month = Client.objects.filter(
        registration_date__gte=month_start_datetime
    ).count()
    
    # Prepare lawyer data for chart
    lawyer_data = []
    for lawyer in top_lawyers:
        lawyer_data.append({
            'name': lawyer.get_full_name() or lawyer.username,
            'clients': lawyer.client_count
        })
    
    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'lawyer_labels': lawyer_labels,
        'lawyer_clients_data': lawyer_clients_data,
        'lawyer_data': json.dumps(lawyer_data),
        'recent_clients': recent_clients,
        'total_documents': total_documents,
        # New summary data
        'recent_client_activities': recent_client_activities,
        'upcoming_client_tasks': formatted_tasks,
        'client_retention_rate': client_retention_rate,
        'avg_response_time': avg_response_time,
        'documents_processed': documents_this_month,
        'new_clients_this_month': new_clients_this_month,
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

class CaseDetailModalView(LoginRequiredMixin, DetailView):
    template_name = "client_management/case_detail_modal.html"
    model = Case
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['case'] = self.object
        context['case_updates'] = self.object.updates.all().order_by('-created_date')[:10]
        context['case_documents'] = self.object.documents.all()
        context['modal_id'] = 'case-detail-modal'
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
    from datetime import datetime, timedelta
    from django.db.models import Avg
    
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
    
    # Additional data for case management summary sections
    current_date = timezone.now().date()
    current_month_start = current_date.replace(day=1)
    
    # Recent case activities (using case updates and status changes)
    recent_case_activities = []
    
    # Add recent case updates
    week_ago = timezone.now() - timedelta(days=7)
    recent_updates = CaseUpdate.objects.filter(
        created_date__gte=week_ago
    ).select_related('case', 'case__client').order_by('-created_date')[:3]
    
    for update in recent_updates:
        recent_case_activities.append({
            'description': f'Case update for "{update.case.title}"',
            'created_at': update.created_date,
            'color': 'blue'
        })
    
    # Add recently created cases
    recent_new_cases = Case.objects.filter(
        created_date__gte=week_ago
    ).select_related('client').order_by('-created_date')[:3]
    
    for case in recent_new_cases:
        recent_case_activities.append({
            'description': f'New case "{case.title}" created',
            'created_at': case.created_date,
            'color': 'green'
        })
    
    # Add recently completed cases
    recent_completed = Case.objects.filter(
        status='completed',
        updated_date__gte=week_ago
    ).select_related('client').order_by('-updated_date')[:2]
    
    for case in recent_completed:
        recent_case_activities.append({
            'description': f'Case "{case.title}" completed',
            'created_at': case.updated_date,
            'color': 'purple'
        })
    
    # Sort activities by date
    recent_case_activities.sort(key=lambda x: x['created_at'], reverse=True)
    recent_case_activities = recent_case_activities[:4]
    
    # Upcoming deadlines
    thirty_days_ahead = current_date + timedelta(days=30)
    upcoming_deadlines = Case.objects.filter(
        expected_completion_date__gte=current_date,
        expected_completion_date__lte=thirty_days_ahead,
        status__in=['pending', 'active', 'on_hold']
    ).select_related('client').order_by('expected_completion_date')[:3]
    
    # Format deadlines for template
    formatted_deadlines = []
    for case in upcoming_deadlines:
        priority_color = {
            'high': 'red',
            'medium': 'yellow',
            'low': 'green'
        }.get(case.priority, 'gray')
        
        formatted_deadlines.append({
            'title': case.title,
            'case_number': case.code,
            'due_date': case.expected_completion_date,
            'priority': case.priority.title(),
            'priority_color': priority_color
        })
    
    # Performance metrics
    # Case success rate (completed vs total)
    case_success_rate = round((completed_cases / total_cases * 100) if total_cases > 0 else 0)
    
    # Average case duration (for completed cases)
    completed_cases_with_duration = Case.objects.filter(
        status='completed',
        created_date__isnull=False,
        updated_date__isnull=False
    )
    
    if completed_cases_with_duration.exists():
        total_duration = sum([
            (case.updated_date - case.created_date).days 
            for case in completed_cases_with_duration
        ])
        avg_case_duration = round(total_duration / completed_cases_with_duration.count() / 30.44, 1)  # Convert to months
    else:
        avg_case_duration = 0
    
    # Cases resolved this month
    month_start_datetime = timezone.make_aware(datetime.combine(current_month_start, datetime.min.time()))
    cases_resolved_this_month = Case.objects.filter(
        status='completed',
        updated_date__gte=month_start_datetime
    ).count()
    
    # Billable hours (mock data - you can implement actual tracking)
    billable_hours_mtd = 0  # This would come from time tracking system
    
    # Case load status
    if overdue_cases > 5:
        case_load_status = "High case load - consider resource allocation"
    elif overdue_cases > 2:
        case_load_status = "Moderate case load - monitor closely"
    else:
        case_load_status = "Case load is within optimal range"
    
    # Approaching deadlines count
    seven_days_ahead = current_date + timedelta(days=7)
    approaching_deadlines_count = Case.objects.filter(
        expected_completion_date__gte=current_date,
        expected_completion_date__lte=seven_days_ahead,
        status__in=['pending', 'active', 'on_hold']
    ).count()
    
    # Get case counts by priority
    low_priority_cases = Case.objects.filter(priority='low').count()
    medium_priority_cases = Case.objects.filter(priority='medium').count()
    high_priority_cases = Case.objects.filter(priority='high').count()
    urgent_priority_cases = Case.objects.filter(priority='urgent').count()
    
    # Prepare lawyer case data for chart
    lawyer_case_data = []
    for lawyer in top_lawyers:
        lawyer_case_data.append({
            'name': lawyer.get_full_name() or lawyer.username,
            'cases': lawyer.case_count
        })
    
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
        # Priority case counts for chart
        'low_priority_cases': low_priority_cases,
        'medium_priority_cases': medium_priority_cases,
        'high_priority_cases': high_priority_cases,
        'urgent_priority_cases': urgent_priority_cases,
        # Lawyer case data for chart
        'lawyer_case_data': json.dumps(lawyer_case_data),
        # New summary data
        'recent_case_activities': recent_case_activities,
        'upcoming_deadlines': formatted_deadlines,
        'case_success_rate': case_success_rate,
        'avg_case_duration': avg_case_duration,
        'cases_resolved_this_month': cases_resolved_this_month,
        'billable_hours_mtd': billable_hours_mtd,
        'case_load_status': case_load_status,
        'approaching_deadlines_count': approaching_deadlines_count,
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

# Court Diary Views

@login_required
@user_passes_test(is_staff)
def court_diary(request):
    from django.utils import timezone
    from datetime import datetime, timedelta
    import calendar
    
    # Get current month and year from request or default to current
    current_date = timezone.now().date()
    year = int(request.GET.get('year', current_date.year))
    month = int(request.GET.get('month', current_date.month))
    
    # Create date objects for the month
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Get cases with court dates in this month
    cases_with_court_dates = Case.objects.filter(
        court_date__gte=first_day,
        court_date__lte=last_day
    ).select_related('client').order_by('court_date')
    
    # Group cases by date
    cases_by_date = {}
    for case in cases_with_court_dates:
        date_key = case.court_date.strftime('%Y-%m-%d')
        if date_key not in cases_by_date:
            cases_by_date[date_key] = []
        cases_by_date[date_key].append(case)
    
    # Generate calendar data
    cal = calendar.monthcalendar(year, month)
    calendar_data = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': None, 'cases': [], 'is_empty': True})
            else:
                date_obj = datetime(year, month, day).date()
                date_key = date_obj.strftime('%Y-%m-%d')
                week_data.append({
                    'day': day,
                    'date': date_obj,
                    'cases': cases_by_date.get(date_key, []),
                    'is_today': date_obj == current_date,
                    'is_empty': False
                })
        calendar_data.append(week_data)
    
    # Navigation dates
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    # Group cases by date for the list view
    court_dates_by_date = {}
    for case in cases_with_court_dates:
        date_key = case.court_date.date()
        if date_key not in court_dates_by_date:
            court_dates_by_date[date_key] = []
        court_dates_by_date[date_key].append(case)
    
    context = {
        'calendar_data': calendar_data,
        'current_month': calendar.month_name[month],
        'current_year': year,
        'current_month_num': month,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'cases_with_court_dates': cases_with_court_dates,
        'court_dates_by_date': court_dates_by_date,
        'total_court_dates': len(cases_with_court_dates),
    }
    
    return render(request, 'client_management/court_diary.html', context)

# Court Date Management Views

class CourtDateUpdateView(LoginRequiredMixin, UpdateView):
    model = Case
    form_class = CourtDateForm
    template_name = 'client_management/court_date_form.html'
    context_object_name = 'case'
    
    def get_success_url(self):
        messages.success(self.request, f"Court date updated successfully for case {self.object.code}.")
        return reverse_lazy('client_management:case_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Log the court date change as a case update
        old_court_date = Case.objects.get(pk=self.object.pk).court_date
        response = super().form_valid(form)
        
        # Create a case update entry
        CaseUpdate.objects.create(
            case=self.object,
            title="Court Date Updated",
            description=f"Court date changed from {old_court_date or 'Not set'} to {self.object.court_date}",
            update_type="court",
            created_by=self.request.user
        )
        
        return response

@login_required
@user_passes_test(is_staff)
def postpone_court_date(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        form = CourtDateForm(request.POST, instance=case)
        if form.is_valid():
            old_court_date = case.court_date
            form.save()
            
            # Create a case update entry for postponement
            CaseUpdate.objects.create(
                case=case,
                title="Court Date Postponed",
                description=f"Court date postponed from {old_court_date} to {case.court_date}. Location: {case.court_location or 'Not specified'}",
                update_type="court",
                created_by=request.user
            )
            
            messages.success(request, f"Court date postponed successfully for case {case.code}.")
            
            # Handle HTMX requests
            if request.headers.get('HX-Request'):
                response = HttpResponse(status=204)
                response["HX-Redirect"] = reverse_lazy('client_management:court_diary')
                return response
            
            return redirect('client_management:court_diary')
    else:
        form = CourtDateForm(instance=case)
    
    context = {
        'form': form,
        'case': case,
        'action': 'postpone',
        'modal_id': 'postpone-court-date-modal'
    }
    
    # Handle HTMX requests for GET (modal content)
    if request.headers.get('HX-Request'):
        return render(request, 'client_management/postpone_court_date_modal.html', context)
    
    return render(request, 'client_management/court_date_form.html', context)

@login_required
@user_passes_test(is_staff)
def add_court_date(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        form = CourtDateForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            
            # Create a case update entry
            CaseUpdate.objects.create(
                case=case,
                title="Court Date Added",
                description=f"Court date set to {case.court_date}. Location: {case.court_location or 'Not specified'}",
                update_type="court",
                created_by=request.user
            )
            
            messages.success(request, f"Court date added successfully for case {case.code}.")
            
            # Handle HTMX requests
            if request.headers.get('HX-Request'):
                response = HttpResponse(status=204)
                response["HX-Redirect"] = reverse_lazy('client_management:case_detail', kwargs={'pk': case.pk})
                return response
            
            return redirect('client_management:case_detail', pk=case.pk)
    else:
        form = CourtDateForm(instance=case)
    
    context = {
        'form': form,
        'case': case,
        'action': 'add'
    }
    
    return render(request, 'client_management/court_date_form.html', context)

@login_required
@user_passes_test(is_staff)
def remove_court_date(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        old_court_date = case.court_date
        old_court_location = case.court_location
        
        case.court_date = None
        case.court_location = None
        case.save()
        
        # Create a case update entry
        CaseUpdate.objects.create(
            case=case,
            title="Court Date Removed",
            description=f"Court date {old_court_date} at {old_court_location or 'unspecified location'} has been removed",
            update_type="court",
            created_by=request.user
        )
        
        messages.success(request, f"Court date removed successfully for case {case.code}.")
        
        # Handle HTMX requests
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse_lazy('client_management:case_detail', kwargs={'pk': case.pk})
            return response
        
        return redirect('client_management:case_detail', pk=case.pk)
    
    return redirect('client_management:case_detail', pk=case.pk)
