#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

from client_management.models import Case
from client_management.views import CaseListView
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import HttpRequest

print('=== Debug Case List View ===')

# Create a mock request
factory = RequestFactory()
request = factory.get('/client-management/cases/')

# Get a staff user
staff_user = User.objects.filter(is_staff=True).first()
if staff_user:
    request.user = staff_user
    print(f'Using user: {staff_user.username} (is_staff: {staff_user.is_staff})')
else:
    print('No staff user found!')
    sys.exit(1)

# Create the view instance
view = CaseListView()
view.setup(request)

# Get the queryset
queryset = view.get_queryset()
print(f'\nQueryset count: {queryset.count()}')
print('Cases in queryset:')
for case in queryset:
    print(f'  - {case.code}: {case.title} (Client: {case.client.name})')

# Get context data
context = view.get_context_data()
print(f'\nContext cases count: {len(context["cases"])}')
print('Cases in context:')
for case in context['cases']:
    print(f'  - {case.code}: {case.title} (Client: {case.client.name})')

print(f'\nOther context data:')
print(f'  - pending_cases: {context.get("pending_cases", "N/A")}')
print(f'  - active_cases: {context.get("active_cases", "N/A")}')
print(f'  - completed_cases: {context.get("completed_cases", "N/A")}')
print(f'  - total_cases: {context.get("total_cases", "N/A")}')