#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

from django.contrib.auth.models import User
from client_portal.models import ClientProfile
from lawyer_portal.models import LawyerProfile

print('=== All Users ===')
for user in User.objects.all():
    print(f'User: {user.username} ({user.get_full_name()})')
    print(f'  - Email: {user.email}')
    print(f'  - Is Staff: {user.is_staff}')
    print(f'  - Is Superuser: {user.is_superuser}')
    print(f'  - Is Active: {user.is_active}')
    print(f'  - Last Login: {user.last_login}')
    
    # Check if user is a client
    try:
        client_profile = ClientProfile.objects.get(user=user)
        print(f'  - Client Profile: {client_profile.client.name}')
    except ClientProfile.DoesNotExist:
        print(f'  - Client Profile: None')
    
    # Check if user is a lawyer
    try:
        lawyer_profile = LawyerProfile.objects.get(user=user)
        print(f'  - Lawyer Profile: Yes')
    except LawyerProfile.DoesNotExist:
        print(f'  - Lawyer Profile: None')
    
    print()