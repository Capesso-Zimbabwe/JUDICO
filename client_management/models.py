from django.db import models
from django.contrib.auth.models import User

# Add to existing models.py
from lawyer_portal.models import LawyerProfile

class Client(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    registration_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    assigned_lawyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_clients')
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')
    
    def __str__(self):
        return self.name

class ClientDocument(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='client_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.client.name} - {self.title}"
