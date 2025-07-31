#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

from client_management.models import Case
from django.contrib.auth.models import User
from client_portal.models import ClientProfile

print('=== Case Permissions Analysis ===')

# Check all cases
all_cases = Case.objects.all()
print(f'Total cases in database: {all_cases.count()}')
for case in all_cases:
    print(f'  - {case.code}: {case.title}')
    print(f'    Client: {case.client.name}')
    print(f'    Status: {case.status}')
    print(f'    Created by: {case.created_by}')
    print(f'    Assigned lawyer: {case.assigned_lawyer}')
    print()

# Check user types and their potential access
print('=== User Analysis ===')
for user in User.objects.all():
    print(f'User: {user.username} ({user.get_full_name()})')
    print(f'  - Is Staff: {user.is_staff}')
    print(f'  - Is Superuser: {user.is_superuser}')
    print(f'  - Is Active: {user.is_active}')
    
    # Check if user has client profile
    try:
        client_profile = ClientProfile.objects.get(user=user)
        print(f'  - Has Client Profile: Yes (Client: {client_profile.client.name})')
        # Check cases for this client
        user_cases = Case.objects.filter(client=client_profile.client)
        print(f'  - Cases for this client: {user_cases.count()}')
        for case in user_cases:
            print(f'    * {case.code}: {case.title}')
    except ClientProfile.DoesNotExist:
        print(f'  - Has Client Profile: No')
    
    # Check cases created by this user
    created_cases = Case.objects.filter(created_by=user)
    print(f'  - Cases created by user: {created_cases.count()}')
    
    # Check cases assigned to this user
    assigned_cases = Case.objects.filter(assigned_lawyer=user)
    print(f'  - Cases assigned to user: {assigned_cases.count()}')
    print()

print('=== Potential Issues ===')
# Check if there are any cases without proper relationships
orphan_cases = Case.objects.filter(created_by__isnull=True)
print(f'Cases without created_by: {orphan_cases.count()}')

unassigned_cases = Case.objects.filter(assigned_lawyer__isnull=True)
print(f'Cases without assigned lawyer: {unassigned_cases.count()}')

inactive_client_cases = Case.objects.filter(client__is_active=False)
print(f'Cases with inactive clients: {inactive_client_cases.count()}')