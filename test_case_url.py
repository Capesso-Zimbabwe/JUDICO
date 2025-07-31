#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

print('=== Testing Case List URL Access ===')

# Create a test client
client = Client()

# Get a staff user
staff_user = User.objects.filter(is_staff=True).first()
if not staff_user:
    print('No staff user found!')
    sys.exit(1)

print(f'Using user: {staff_user.username} (is_staff: {staff_user.is_staff})')

# Login the user
login_success = client.force_login(staff_user)
print(f'Login successful: {login_success is None}')  # force_login returns None on success

# Test the case list URL
case_list_url = reverse('client_management:case_list')
print(f'Case list URL: {case_list_url}')

response = client.get(case_list_url)
print(f'Response status code: {response.status_code}')

if response.status_code == 200:
    print('Success! Page loaded correctly.')
    # Check if cases are in the response content
    content = response.content.decode('utf-8')
    if 'CS000007' in content:
        print('✓ Case CS000007 found in response')
    else:
        print('✗ Case CS000007 NOT found in response')
    
    if 'CS000006' in content:
        print('✓ Case CS000006 found in response')
    else:
        print('✗ Case CS000006 NOT found in response')
    
    if 'CS000005' in content:
        print('✓ Case CS000005 found in response')
    else:
        print('✗ Case CS000005 NOT found in response')
    
    # Check for table content
    if 'casesTable' in content:
        print('✓ Cases table found in response')
    else:
        print('✗ Cases table NOT found in response')
        
    # Check for "No cases" message
    if 'no cases' in content.lower() or 'no data' in content.lower():
        print('⚠ "No cases" message found in response')
    
else:
    print(f'Error! Status code: {response.status_code}')
    if hasattr(response, 'content'):
        print(f'Response content: {response.content.decode("utf-8")[:500]}...')