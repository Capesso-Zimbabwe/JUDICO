from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

class DocumentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-folder')
    color = models.CharField(max_length=20, default='blue')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Document Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def document_count(self):
        return self.documents.count()
    
    @property
    def total_size(self):
        total = 0
        for doc in self.documents.all():
            if doc.file and os.path.exists(doc.file.path):
                total += doc.file.size
        return total

class Document(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('doc', 'Word Document'),
        ('docx', 'Word Document (DOCX)'),
        ('xls', 'Excel Spreadsheet'),
        ('xlsx', 'Excel Spreadsheet (XLSX)'),
        ('ppt', 'PowerPoint Presentation'),
        ('pptx', 'PowerPoint Presentation (PPTX)'),
        ('txt', 'Text File'),
        ('jpg', 'JPEG Image'),
        ('png', 'PNG Image'),
        ('gif', 'GIF Image'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/%Y/%m/')
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='documents')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='other')
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    access_count = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['file_type']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def file_size(self):
        if self.file and os.path.exists(self.file.path):
            return self.file.size
        return 0
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def file_extension(self):
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''
    
    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def increment_access_count(self):
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])

class DocumentAccess(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['document', 'accessed_at']),
            models.Index(fields=['user', 'accessed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} accessed {self.document.title} at {self.accessed_at}"
