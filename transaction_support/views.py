from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView, ListView
from django.db.models import Count, Q, Sum
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    Transaction, TransactionEntity, EntityOwnershipHistory,
    TransactionDocument, DueDiligenceCategory, TransactionWorkflow,
    TransactionTask, TransactionAuditLog, TransactionReport, ContractReassignment
)
from .forms import (
    TransactionForm, TransactionFilterForm, TransactionEntityForm,
    EntityOwnershipHistoryForm, TransactionDocumentForm, DueDiligenceCategoryForm,
    TransactionWorkflowForm, TransactionTaskForm, TransactionReportForm,
    ContractReassignmentForm, BulkDocumentUploadForm
)
from JUDICO_HUB import settings

# Helper function to check if user is staff
def is_staff(user):
    return user.is_staff

@login_required
def transaction_dashboard(request):
    """Main dashboard for transaction support with key metrics and recent activity"""
    
    # Get transaction statistics
    total_transactions = Transaction.objects.count()
    active_transactions = Transaction.objects.filter(status__in=['planning', 'due_diligence', 'negotiation', 'documentation']).count()
    completed_transactions = Transaction.objects.filter(status='completed').count()
    
    # Recent transactions
    recent_transactions = Transaction.objects.order_by('-created_at')[:5]
    
    # Upcoming deadlines
    upcoming_deadlines = TransactionTask.objects.filter(
        due_date__gte=timezone.now(),
        due_date__lte=timezone.now() + timedelta(days=7),
        status__in=['pending', 'in_progress']
    ).order_by('due_date')[:10]
    
    # Transaction value by type
    transaction_values = Transaction.objects.values('transaction_type').annotate(
        total_value=Sum('transaction_value'),
        count=Count('id')
    )
    
    # High priority tasks
    high_priority_tasks = TransactionTask.objects.filter(
        priority='high',
        status__in=['pending', 'in_progress']
    ).count()
    
    context = {
        'total_transactions': total_transactions,
        'active_transactions': active_transactions,
        'completed_transactions': completed_transactions,
        'recent_transactions': recent_transactions,
        'upcoming_deadlines': upcoming_deadlines,
        'transaction_values': transaction_values,
        'high_priority_tasks': high_priority_tasks,
    }
    
    return render(request, 'transaction_support/dashboard.html', context)


class TransactionListView(LoginRequiredMixin, ListView):
    """List view for transactions with filtering and pagination"""
    template_name = "transaction_support/transaction_list.html"
    paginate_by = settings.PAGINATE_BY
    model = Transaction
    context_object_name = 'transactions'
    ordering = '-created_at'

    def get_queryset(self):
        queryset = Transaction.objects.all().order_by('-created_at')
        
        # Search functionality
        if search_param := self.request.GET.get('search'):
            queryset = queryset.filter(
                Q(title__icontains=search_param) |
                Q(transaction_code__icontains=search_param) |
                Q(client__name__icontains=search_param) |
                Q(description__icontains=search_param)
            )
        
        # Filter by status
        if status := self.request.GET.get('status'):
            queryset = queryset.filter(status=status)
        
        # Filter by transaction type
        if transaction_type := self.request.GET.get('transaction_type'):
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by priority
        if priority := self.request.GET.get('priority'):
            queryset = queryset.filter(priority=priority)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter form
        initial = {}
        for param in ['search', 'status', 'transaction_type', 'priority']:
            if value := self.request.GET.get(param):
                initial[param] = value
        
        context['filter_form'] = TransactionFilterForm(initial=initial)
        
        # Add statistics
        context['total_transactions'] = Transaction.objects.count()
        context['active_transactions'] = Transaction.objects.filter(
            status__in=['planning', 'due_diligence', 'negotiation', 'documentation']
        ).count()
        
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Detailed view for a single transaction"""
    template_name = "transaction_support/transaction_detail.html"
    model = Transaction
    context_object_name = 'transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction = self.get_object()
        
        # Get related data
        context['entities'] = transaction.entities.all()
        context['documents'] = transaction.documents.all()[:10]  # Latest 10 documents
        context['workflows'] = transaction.workflows.all()
        context['recent_tasks'] = TransactionTask.objects.filter(
            workflow__transaction=transaction
        ).order_by('-created_at')[:5]
        context['audit_logs'] = transaction.audit_logs.order_by('-timestamp')[:10]
        
        # Task statistics
        all_tasks = TransactionTask.objects.filter(workflow__transaction=transaction)
        context['task_stats'] = {
            'total': all_tasks.count(),
            'completed': all_tasks.filter(status='completed').count(),
            'in_progress': all_tasks.filter(status='in_progress').count(),
            'pending': all_tasks.filter(status='pending').count(),
        }
        
        return context


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create new transaction"""
    template_name = "transaction_support/transaction_form.html"
    model = Transaction
    form_class = TransactionForm
    success_url = reverse_lazy('transaction_support:transaction_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Create audit log
        TransactionAuditLog.objects.create(
            transaction=self.object,
            user=self.request.user,
            action='created',
            description=f'Transaction "{self.object.title}" created'
        )
        
        messages.success(self.request, f'Transaction "{self.object.title}" created successfully.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing transaction"""
    template_name = "transaction_support/transaction_form.html"
    model = Transaction
    form_class = TransactionForm
    success_url = reverse_lazy('transaction_support:transaction_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Create audit log
        TransactionAuditLog.objects.create(
            transaction=self.object,
            user=self.request.user,
            action='updated',
            description=f'Transaction "{self.object.title}" updated'
        )
        
        messages.success(self.request, f'Transaction "{self.object.title}" updated successfully.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


@login_required
@user_passes_test(is_staff)
def transaction_delete(request, pk):
    """Delete transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    if request.method == 'POST':
        title = transaction.title
        transaction.delete()
        messages.success(request, f'Transaction "{title}" deleted successfully.')
        return redirect('transaction_support:transaction_list')
    
    return render(request, 'transaction_support/transaction_confirm_delete.html', {
        'transaction': transaction
    })


class TransactionEntityCreateView(LoginRequiredMixin, CreateView):
    """Add entity to transaction"""
    template_name = "transaction_support/entity_form.html"
    model = TransactionEntity
    form_class = TransactionEntityForm

    def dispatch(self, request, *args, **kwargs):
        self.transaction = get_object_or_404(Transaction, pk=kwargs['transaction_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.transaction = self.transaction
        response = super().form_valid(form)
        
        # Create audit log
        TransactionAuditLog.objects.create(
            transaction=self.transaction,
            user=self.request.user,
            action='entity_added',
            description=f'Entity "{self.object.entity_name}" added to transaction'
        )
        
        messages.success(self.request, f'Entity "{self.object.entity_name}" added successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('transaction_support:transaction_detail', kwargs={'pk': self.transaction.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.transaction
        return context


class TransactionDocumentCreateView(LoginRequiredMixin, CreateView):
    """Upload document to transaction"""
    template_name = "transaction_support/document_form.html"
    model = TransactionDocument
    form_class = TransactionDocumentForm

    def dispatch(self, request, *args, **kwargs):
        self.transaction = get_object_or_404(Transaction, pk=kwargs['transaction_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.transaction = self.transaction
        form.instance.uploaded_by = self.request.user
        response = super().form_valid(form)
        
        # Create audit log
        TransactionAuditLog.objects.create(
            transaction=self.transaction,
            user=self.request.user,
            action='document_uploaded',
            description=f'Document "{self.object.title}" uploaded'
        )
        
        messages.success(self.request, f'Document "{self.object.title}" uploaded successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('transaction_support:transaction_detail', kwargs={'pk': self.transaction.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.transaction
        return context


@login_required
def bulk_document_upload(request, transaction_pk):
    """Bulk upload documents to transaction"""
    transaction = get_object_or_404(Transaction, pk=transaction_pk)
    
    if request.method == 'POST':
        form = BulkDocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            documents = request.FILES.getlist('documents')
            category = form.cleaned_data.get('category')
            access_level = form.cleaned_data['access_level']
            is_confidential = form.cleaned_data['is_confidential']
            
            uploaded_count = 0
            for document in documents:
                TransactionDocument.objects.create(
                    transaction=transaction,
                    title=document.name,
                    document=document,
                    due_diligence_category=category,
                    access_level=access_level,
                    is_confidential=is_confidential,
                    uploaded_by=request.user
                )
                uploaded_count += 1
            
            # Create audit log
            TransactionAuditLog.objects.create(
                transaction=transaction,
                user=request.user,
                action='bulk_upload',
                description=f'{uploaded_count} documents uploaded in bulk'
            )
            
            messages.success(request, f'{uploaded_count} documents uploaded successfully.')
            return redirect('transaction_support:transaction_detail', pk=transaction.pk)
    else:
        form = BulkDocumentUploadForm()
    
    return render(request, 'transaction_support/bulk_upload.html', {
        'form': form,
        'transaction': transaction
    })


class TransactionWorkflowCreateView(LoginRequiredMixin, CreateView):
    """Create workflow for transaction"""
    template_name = "transaction_support/workflow_form.html"
    model = TransactionWorkflow
    form_class = TransactionWorkflowForm

    def dispatch(self, request, *args, **kwargs):
        self.transaction = get_object_or_404(Transaction, pk=kwargs['transaction_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.transaction = self.transaction
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Auto-generate default tasks based on transaction type
        self._create_default_tasks()
        
        # Create audit log
        TransactionAuditLog.objects.create(
            transaction=self.transaction,
            user=self.request.user,
            action='workflow_created',
            description=f'Workflow "{self.object.name}" created'
        )
        
        messages.success(self.request, f'Workflow "{self.object.name}" created successfully.')
        return response

    def _create_default_tasks(self):
        """Create default tasks based on transaction type"""
        workflow = self.object
        transaction_type = self.transaction.transaction_type
        
        # Default tasks for different transaction types
        default_tasks = {
            'merger': [
                ('Initial Due Diligence', 'due_diligence', 'high', 7),
                ('Legal Review', 'legal_review', 'high', 14),
                ('Financial Analysis', 'financial_review', 'medium', 10),
                ('Regulatory Approval', 'regulatory', 'high', 30),
                ('Documentation Preparation', 'documentation', 'medium', 21),
                ('Closing Preparation', 'closing', 'high', 7),
            ],
            'acquisition': [
                ('Target Identification', 'due_diligence', 'high', 14),
                ('Valuation Analysis', 'financial_review', 'high', 10),
                ('Due Diligence Review', 'due_diligence', 'high', 21),
                ('Purchase Agreement', 'documentation', 'high', 14),
                ('Regulatory Filing', 'regulatory', 'medium', 30),
                ('Closing', 'closing', 'high', 7),
            ],
            'financing': [
                ('Credit Analysis', 'financial_review', 'high', 7),
                ('Documentation Review', 'documentation', 'high', 14),
                ('Compliance Check', 'compliance', 'high', 10),
                ('Approval Process', 'approval', 'high', 21),
                ('Funding Preparation', 'closing', 'medium', 7),
            ]
        }
        
        tasks = default_tasks.get(transaction_type, [])
        for i, (title, task_type, priority, days_offset) in enumerate(tasks):
            due_date = timezone.now() + timedelta(days=days_offset)
            TransactionTask.objects.create(
                workflow=workflow,
                title=title,
                description=f'Default {task_type} task for {transaction_type}',
                task_type=task_type,
                priority=priority,
                due_date=due_date,
                sort_order=i + 1
            )

    def get_success_url(self):
        return reverse_lazy('transaction_support:transaction_detail', kwargs={'pk': self.transaction.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.transaction
        return context


class TransactionTaskCreateView(LoginRequiredMixin, CreateView):
    """Create task for transaction workflow"""
    template_name = "transaction_support/task_form.html"
    model = TransactionTask
    form_class = TransactionTaskForm

    def dispatch(self, request, *args, **kwargs):
        self.workflow = get_object_or_404(TransactionWorkflow, pk=kwargs['workflow_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['transaction'] = self.workflow.transaction
        return kwargs

    def form_valid(self, form):
        form.instance.workflow = self.workflow
        response = super().form_valid(form)
        
        # Create audit log
        TransactionAuditLog.objects.create(
            transaction=self.workflow.transaction,
            user=self.request.user,
            action='task_created',
            description=f'Task "{self.object.title}" created'
        )
        
        messages.success(self.request, f'Task "{self.object.title}" created successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy('transaction_support:transaction_detail', kwargs={'pk': self.workflow.transaction.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow'] = self.workflow
        context['transaction'] = self.workflow.transaction
        return context


@login_required
def task_update_status(request, task_pk):
    """Update task status via AJAX"""
    task = get_object_or_404(TransactionTask, pk=task_pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(TransactionTask.STATUS_CHOICES):
            old_status = task.status
            task.status = new_status
            
            if new_status == 'completed':
                task.completed_date = timezone.now()
                task.completed_by = request.user
            
            task.save()
            
            # Create audit log
            TransactionAuditLog.objects.create(
                transaction=task.workflow.transaction,
                user=request.user,
                action='task_status_updated',
                description=f'Task "{task.title}" status changed from {old_status} to {new_status}'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Task status updated to {new_status}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def transaction_reports(request):
    """Generate transaction reports"""
    if request.method == 'POST':
        form = TransactionReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            report.save()
            
            # Generate report data based on type
            report_data = _generate_report_data(report)
            
            return render(request, 'transaction_support/report_result.html', {
                'report': report,
                'report_data': report_data
            })
    else:
        form = TransactionReportForm()
    
    return render(request, 'transaction_support/reports.html', {
        'form': form
    })


def _generate_report_data(report):
    """Generate report data based on report type"""
    data = {}
    
    # Base queryset
    transactions = Transaction.objects.all()
    
    # Apply date filters
    if report.date_from:
        transactions = transactions.filter(created_at__gte=report.date_from)
    if report.date_to:
        transactions = transactions.filter(created_at__lte=report.date_to)
    
    # Apply confidentiality filter
    if not report.include_confidential:
        transactions = transactions.filter(is_confidential=False)
    
    if report.report_type == 'summary':
        data = {
            'total_transactions': transactions.count(),
            'by_status': transactions.values('status').annotate(count=Count('id')),
            'by_type': transactions.values('transaction_type').annotate(count=Count('id')),
            'total_value': transactions.aggregate(total=Sum('transaction_value'))['total'] or 0,
        }
    
    elif report.report_type == 'detailed':
        data = {
            'transactions': transactions.select_related('client', 'lead_lawyer').order_by('-created_at'),
            'total_count': transactions.count(),
        }
    
    elif report.report_type == 'performance':
        # Calculate performance metrics
        completed_transactions = transactions.filter(status='completed')
        data = {
            'completion_rate': (completed_transactions.count() / transactions.count() * 100) if transactions.count() > 0 else 0,
            'avg_completion_time': completed_transactions.aggregate(
                avg_time=Count('id')  # This would need more complex calculation
            ),
            'overdue_tasks': TransactionTask.objects.filter(
                workflow__transaction__in=transactions,
                due_date__lt=timezone.now(),
                status__in=['pending', 'in_progress']
            ).count(),
        }
    
    return data


# Legacy view functions for backward compatibility
@login_required
def transaction_list(request):
    """Legacy function-based view - redirects to class-based view"""
    return redirect('transaction_support:transaction_list_cbv')

@login_required
def transaction_create(request):
    """Legacy function-based view - redirects to class-based view"""
    return redirect('transaction_support:transaction_create_cbv')

@login_required
def transaction_monitoring(request):
    """Transaction monitoring dashboard"""
    # Get active transactions with their progress
    active_transactions = Transaction.objects.filter(
        status__in=['planning', 'due_diligence', 'negotiation', 'documentation']
    ).select_related('client', 'lead_lawyer')
    
    # Get overdue tasks
    overdue_tasks = TransactionTask.objects.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).select_related('workflow__transaction')
    
    # Get upcoming deadlines
    upcoming_deadlines = TransactionTask.objects.filter(
        due_date__gte=timezone.now(),
        due_date__lte=timezone.now() + timedelta(days=30),
        status__in=['pending', 'in_progress']
    ).order_by('due_date')
    
    context = {
        'active_transactions': active_transactions,
        'overdue_tasks': overdue_tasks,
        'upcoming_deadlines': upcoming_deadlines,
    }
    
    return render(request, 'transaction_support/monitoring.html', context)


class TransactionDocumentListView(LoginRequiredMixin, ListView):
    """List all documents for a transaction"""
    template_name = "transaction_support/document_list.html"
    model = TransactionDocument
    context_object_name = 'documents'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.transaction = get_object_or_404(Transaction, pk=kwargs['transaction_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = TransactionDocument.objects.filter(transaction=self.transaction)
        
        # Filter by document type
        document_type = self.request.GET.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        # Filter by access level
        access_level = self.request.GET.get('access_level')
        if access_level:
            queryset = queryset.filter(access_level=access_level)
        
        # Search by title or description
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.select_related('uploaded_by', 'reviewed_by').order_by('-uploaded_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.transaction
        context['document_types'] = TransactionDocument.DOCUMENT_TYPES
        context['access_levels'] = TransactionDocument.ACCESS_LEVELS
        return context


class TransactionDocumentDetailView(LoginRequiredMixin, DetailView):
    """Detailed view for a document with version history"""
    template_name = "transaction_support/document_detail.html"
    model = TransactionDocument
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.get_object()
        
        # Get version history
        context['versions'] = TransactionDocument.objects.filter(
            Q(parent_document=document) | Q(pk=document.pk)
        ).order_by('-version')
        
        # Get related documents
        context['related_documents'] = TransactionDocument.objects.filter(
            transaction=document.transaction,
            document_type=document.document_type
        ).exclude(pk=document.pk)[:5]
        
        return context


@login_required
def document_download(request, pk):
    """Download a document file"""
    document = get_object_or_404(TransactionDocument, pk=pk)
    
    # Check access permissions
    if not _has_document_access(request.user, document):
        messages.error(request, 'You do not have permission to access this document.')
        return redirect('transaction_support:transaction_detail', pk=document.transaction.pk)
    
    # Update last accessed timestamp
    document.last_accessed = timezone.now()
    document.save(update_fields=['last_accessed'])
    
    # Create audit log
    TransactionAuditLog.objects.create(
        transaction=document.transaction,
        user=request.user,
        action='document_downloaded',
        description=f'Document "{document.title}" downloaded'
    )
    
    # Serve the file
    response = HttpResponse(document.document_file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.title}"'
    return response


@login_required
def document_version_create(request, pk):
    """Create a new version of an existing document"""
    parent_document = get_object_or_404(TransactionDocument, pk=pk)
    
    if request.method == 'POST':
        form = TransactionDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # Create new version
            new_version = form.save(commit=False)
            new_version.transaction = parent_document.transaction
            new_version.parent_document = parent_document
            new_version.version = parent_document.version + 1
            new_version.uploaded_by = request.user
            new_version.save()
            
            # Copy due diligence categories
            new_version.due_diligence_categories.set(
                parent_document.due_diligence_categories.all()
            )
            
            # Create audit log
            TransactionAuditLog.objects.create(
                transaction=parent_document.transaction,
                user=request.user,
                action='document_version_created',
                description=f'New version {new_version.version} of "{parent_document.title}" uploaded'
            )
            
            messages.success(request, f'New version of "{parent_document.title}" uploaded successfully.')
            return redirect('transaction_support:document_detail', pk=new_version.pk)
    else:
        # Pre-populate form with parent document data
        initial_data = {
            'title': parent_document.title,
            'description': parent_document.description,
            'document_type': parent_document.document_type,
            'access_level': parent_document.access_level,
        }
        form = TransactionDocumentForm(initial=initial_data)
    
    return render(request, 'transaction_support/document_version_form.html', {
        'form': form,
        'parent_document': parent_document,
        'transaction': parent_document.transaction
    })


@login_required
def document_review_toggle(request, pk):
    """Toggle document review status"""
    document = get_object_or_404(TransactionDocument, pk=pk)
    
    if request.method == 'POST':
        if document.is_reviewed:
            document.is_reviewed = False
            document.reviewed_by = None
            document.reviewed_at = None
            action = 'document_review_removed'
            message = f'Review status removed from "{document.title}"'
        else:
            document.is_reviewed = True
            document.reviewed_by = request.user
            document.reviewed_at = timezone.now()
            action = 'document_reviewed'
            message = f'Document "{document.title}" marked as reviewed'
        
        document.save()
        
        # Create audit log
        TransactionAuditLog.objects.create(
            transaction=document.transaction,
            user=request.user,
            action=action,
            description=message
        )
        
        messages.success(request, message)
    
    return redirect('transaction_support:document_detail', pk=document.pk)


def _has_document_access(user, document):
    """Check if user has access to a document based on access level"""
    if user.is_superuser:
        return True
    
    access_level = document.access_level
    transaction = document.transaction
    
    if access_level == 'public':
        return True
    elif access_level == 'team_only':
        # Check if user is part of the transaction team
        return (
            user == transaction.lead_lawyer or
            user == transaction.created_by or
            TransactionTask.objects.filter(
                workflow__transaction=transaction,
                assigned_to=user
            ).exists()
        )
    elif access_level == 'lead_only':
        return user == transaction.lead_lawyer or user == transaction.created_by
    elif access_level == 'confidential':
        return user == transaction.lead_lawyer or user == transaction.created_by
    
    return False
