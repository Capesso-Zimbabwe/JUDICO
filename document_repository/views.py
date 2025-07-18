from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
import os
from .models import Document, DocumentCategory, DocumentAccess

@login_required
def document_dashboard(request):
    # Dashboard statistics
    total_documents = Document.objects.filter(is_active=True).count()
    total_categories = DocumentCategory.objects.count()
    recent_uploads = Document.objects.filter(is_active=True).order_by('-uploaded_at')[:5]
    
    # Calculate total storage
    total_storage = sum(doc.file_size for doc in Document.objects.filter(is_active=True))
    total_storage_mb = round(total_storage / (1024 * 1024), 2)
    
    context = {
        'total_documents': total_documents,
        'total_categories': total_categories,
        'recent_uploads': recent_uploads,
        'total_storage_mb': total_storage_mb,
    }
    return render(request, 'document_repository/dashboard.html', context)

@login_required
def document_list(request):
    documents = Document.objects.filter(is_active=True).select_related('category', 'uploaded_by')
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Filter by category if specified
    category_filter = request.GET.get('category')
    if category_filter:
        documents = documents.filter(category__name__icontains=category_filter)
    
    # Order by most recent first
    documents = documents.order_by('-uploaded_at')
    
    # Pagination
    paginator = Paginator(documents, 12)  # Show 12 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = DocumentCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
    }
    return render(request, 'document_repository/document_list.html', context)

@login_required
def document_upload(request):
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            category_id = request.POST.get('category')
            tags = request.POST.get('tags', '').strip()
            uploaded_file = request.FILES.get('file')
            
            # Validation
            if not title:
                messages.error(request, 'Document title is required.')
                raise ValueError('Title is required')
            
            if not uploaded_file:
                messages.error(request, 'Please select a file to upload.')
                raise ValueError('File is required')
            
            if not category_id:
                messages.error(request, 'Please select a category.')
                raise ValueError('Category is required')
            
            # Get category object
            try:
                category = DocumentCategory.objects.get(id=category_id)
            except DocumentCategory.DoesNotExist:
                messages.error(request, 'Invalid category selected.')
                raise ValueError('Invalid category')
            
            # Determine file type based on extension
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            file_type_mapping = {
                '.pdf': 'pdf',
                '.doc': 'doc',
                '.docx': 'docx',
                '.xls': 'xls',
                '.xlsx': 'xlsx',
                '.ppt': 'ppt',
                '.pptx': 'pptx',
                '.txt': 'txt',
                '.jpg': 'jpg',
                '.jpeg': 'jpg',
                '.png': 'png',
                '.gif': 'gif',
            }
            file_type = file_type_mapping.get(file_extension, 'other')
            
            # Create document
            document = Document.objects.create(
                title=title,
                description=description,
                file=uploaded_file,
                category=category,
                file_type=file_type,
                tags=tags,
                uploaded_by=request.user
            )
            
            messages.success(request, f'Document "{title}" uploaded successfully!')
            return redirect('document_repository:document_detail', document_id=document.id)
            
        except Exception as e:
            # If there was an error and no specific message was set, show a generic error
            if not messages.get_messages(request):
                messages.error(request, 'An error occurred while uploading the document. Please try again.')
    
    categories = DocumentCategory.objects.all().order_by('name')
    context = {'categories': categories}
    return render(request, 'document_repository/document_upload.html', context)

@login_required
def category_list(request):
    categories = DocumentCategory.objects.annotate(
        doc_count=Count('documents')
    ).order_by('name')
    
    context = {'categories': categories}
    return render(request, 'document_repository/category_list.html', context)

@login_required
def document_search(request):
    documents = []
    search_performed = False
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    file_type = request.GET.get('file_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    tags = request.GET.get('tags', '').strip()
    
    if query or category_id or file_type or date_from or date_to or tags:
        search_performed = True
        documents_qs = Document.objects.filter(is_active=True).select_related('category', 'uploaded_by')
        
        # Text search in title and description
        if query:
            documents_qs = documents_qs.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # Category filter
        if category_id:
            try:
                category_id = int(category_id)
                documents_qs = documents_qs.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        
        # File type filter
        if file_type:
            documents_qs = documents_qs.filter(file_type=file_type)
        
        # Date range filter
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                documents_qs = documents_qs.filter(uploaded_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                documents_qs = documents_qs.filter(uploaded_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Tags filter
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            for tag in tag_list:
                documents_qs = documents_qs.filter(tags__icontains=tag)
        
        # Order by relevance (most recent first, then by access count)
        documents_qs = documents_qs.order_by('-uploaded_at', '-access_count')
        
        # Pagination
        paginator = Paginator(documents_qs, 10)  # Show 10 results per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        documents = page_obj
    
    # Get all categories and file types for filters
    categories = DocumentCategory.objects.all().order_by('name')
    file_types = Document.FILE_TYPE_CHOICES
    
    # Search statistics
    total_results = documents.paginator.count if search_performed and documents else 0
    
    context = {
        'documents': documents,
        'search_performed': search_performed,
        'query': query,
        'selected_category': category_id,
        'selected_file_type': file_type,
        'date_from': date_from,
        'date_to': date_to,
        'tags': tags,
        'categories': categories,
        'file_types': file_types,
        'total_results': total_results,
    }
    return render(request, 'document_repository/document_search.html', context)

@login_required
def document_detail(request, document_id):
    document = get_object_or_404(Document, id=document_id, is_active=True)
    
    # Log document access
    DocumentAccess.objects.create(
        document=document,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Increment access count
    document.increment_access_count()
    
    # Get related documents (same category)
    related_documents = Document.objects.filter(
        category=document.category,
        is_active=True
    ).exclude(id=document.id)[:5]
    
    context = {
        'document': document,
        'related_documents': related_documents,
    }
    return render(request, 'document_repository/document_detail.html', context)

@login_required
def search_suggestions(request):
    """AJAX endpoint for search suggestions"""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if query and len(query) >= 2:
        # Get title suggestions
        title_suggestions = Document.objects.filter(
            title__icontains=query,
            is_active=True
        ).values_list('title', flat=True)[:5]
        
        # Get tag suggestions
        tag_documents = Document.objects.filter(
            tags__icontains=query,
            is_active=True
        ).values_list('tags', flat=True)
        
        tag_suggestions = set()
        for tags_str in tag_documents:
            if tags_str:
                tags_list = [tag.strip() for tag in tags_str.split(',')]
                for tag in tags_list:
                    if query.lower() in tag.lower():
                        tag_suggestions.add(tag)
        
        suggestions = list(title_suggestions) + list(tag_suggestions)[:3]
        suggestions = suggestions[:8]  # Limit to 8 suggestions
    
    return JsonResponse({'suggestions': suggestions})
