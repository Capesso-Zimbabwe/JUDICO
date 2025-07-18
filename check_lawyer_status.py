#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

from django.contrib.auth.models import User
from lawyer_portal.models import LawyerProfile

print('=== USER STATUS ===')
users = User.objects.all()
for user in users:
    has_lawyer_profile = hasattr(user, 'lawyer_profile')
    print(f'User: {user.username} | Has lawyer_profile: {has_lawyer_profile} | Is staff: {user.is_staff} | Is superuser: {user.is_superuser}')

print('\n=== LAWYER PROFILES ===')
profiles = LawyerProfile.objects.all()
for profile in profiles:
    print(f'Profile: {profile.user.username} | Specialization: {profile.specialization}')

print('\n=== CURRENT LOGGED IN USER (if any) ===')
# This would need session info, but let's check if there are any active sessions
from django.contrib.sessions.models import Session
from django.utils import timezone

active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
print(f'Active sessions: {active_sessions.count()}')