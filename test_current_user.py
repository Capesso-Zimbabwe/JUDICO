#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone

print('=== Active Sessions ===')
active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
print(f'Total active sessions: {active_sessions.count()}')

for session in active_sessions:
    session_data = session.get_decoded()
    user_id = session_data.get('_auth_user_id')
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            print(f'Session: {session.session_key[:10]}...')
            print(f'  User: {user.username} ({user.get_full_name()})')
            print(f'  Is Staff: {user.is_staff}')
            print(f'  Is Superuser: {user.is_superuser}')
            print(f'  Expires: {session.expire_date}')
            print()
        except User.DoesNotExist:
            print(f'Session {session.session_key[:10]}... has invalid user_id: {user_id}')
    else:
        print(f'Session {session.session_key[:10]}... has no user logged in')

print('\n=== All Cases Summary ===')
from client_management.models import Case
cases = Case.objects.all()
print(f'Total cases in database: {cases.count()}')
for case in cases:
    print(f'  - {case.code}: {case.title} (Client: {case.client.name}, Status: {case.status})')