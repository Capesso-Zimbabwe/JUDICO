from django.db import models
from django.contrib.auth.models import User
from client_management.models import Client
from django.utils import timezone
from django.core.validators import FileExtensionValidator

class Contract(models.Model):
    CONTRACT_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('pending_signature', 'Pending Signature'),
        ('signed', 'Signed'),
        ('executed', 'Executed'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired'),
    ]
    
    CONTRACT_TYPE_CHOICES = [
        ('service_agreement', 'Service Agreement'),
        ('retainer_agreement', 'Retainer Agreement'),
        ('settlement_agreement', 'Settlement Agreement'),
        ('employment_contract', 'Employment Contract'),
        ('partnership_agreement', 'Partnership Agreement'),
        ('nda', 'Non-Disclosure Agreement'),
        ('licensing_agreement', 'Licensing Agreement'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    contract_type = models.CharField(max_length=50, choices=CONTRACT_TYPE_CHOICES)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contracts')
    assigned_lawyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contracts')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_contracts')
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='draft')
    
    # Contract details
    contract_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Document management
    contract_document = models.FileField(
        upload_to='contracts/documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional fields
    notes = models.TextField(blank=True)
    is_template = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.client.name}"
    
    @property
    def is_active(self):
        return self.status in ['signed', 'executed']
    
    @property
    def is_expired(self):
        if self.end_date:
            return timezone.now().date() > self.end_date
        return False
    
    @property
    def days_until_expiry(self):
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return delta.days if delta.days > 0 else 0
        return None

class ContractSignature(models.Model):
    SIGNATURE_TYPE_CHOICES = [
        ('client', 'Client Signature'),
        ('lawyer', 'Lawyer Signature'),
        ('witness', 'Witness Signature'),
        ('notary', 'Notary Signature'),
    ]
    
    SIGNATURE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('signed', 'Signed'),
        ('declined', 'Declined'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='signatures')
    signer_name = models.CharField(max_length=100)
    signer_email = models.EmailField()
    signature_type = models.CharField(max_length=20, choices=SIGNATURE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=SIGNATURE_STATUS_CHOICES, default='pending')
    
    # Signature data
    signature_image = models.ImageField(upload_to='contracts/signatures/', null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional verification
    verification_code = models.CharField(max_length=50, blank=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['contract', 'signer_email', 'signature_type']
        
    def __str__(self):
        return f"{self.signer_name} - {self.contract.title}"

class ContractTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    contract_type = models.CharField(max_length=50, choices=Contract.CONTRACT_TYPE_CHOICES)
    template_content = models.TextField()
    
    # Template file
    template_file = models.FileField(
        upload_to='contracts/templates/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        null=True,
        blank=True
    )
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name

class ContractAmendment(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='amendments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    amendment_document = models.FileField(
        upload_to='contracts/amendments/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        null=True,
        blank=True
    )
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_amendments')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.contract.title}"
