#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

from client_management.models import Case, Client

print('=== Database Check ===')
print(f'Total cases: {Case.objects.count()}')
print(f'Total clients: {Client.objects.count()}')

print('\n=== All Cases ===')
for case in Case.objects.all():
    print(f'  - Case {case.id}: {case.title}')
    print(f'    Client: {case.client.name}')
    print(f'    Status: {case.status}')
    print(f'    Created: {case.created_date}')
    print()

print('=== Clients without cases ===')
clients_without_cases = Client.objects.filter(cases__isnull=True).distinct()
print(f'Count: {clients_without_cases.count()}')
for client in clients_without_cases:
    print(f'  - Client {client.id}: {client.name}')

print('=== Clients with cases ===')
clients_with_cases = Client.objects.filter(cases__isnull=False).distinct()
print(f'Count: {clients_with_cases.count()}')
for client in clients_with_cases:
    print(f'  - Client {client.id}: {client.name} ({client.cases.count()} cases)')