from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from client_management.models import Client, Case

class Command(BaseCommand):
    help = 'Create initial cases for existing clients who do not have any cases'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating cases',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all clients who don't have any cases
        clients_without_cases = Client.objects.filter(cases__isnull=True).distinct()
        
        if not clients_without_cases.exists():
            self.stdout.write(
                self.style.SUCCESS('All existing clients already have cases.')
            )
            return
        
        created_count = 0
        
        for client in clients_without_cases:
            if dry_run:
                self.stdout.write(
                    f'Would create case for client: {client.name} (ID: {client.id})'
                )
            else:
                # Try to get the user who created the client, fallback to first superuser
                try:
                    created_by = client.client_profile.user if hasattr(client, 'client_profile') else None
                    if not created_by:
                        created_by = User.objects.filter(is_superuser=True).first()
                        if not created_by:
                            created_by = User.objects.first()
                except:
                    created_by = User.objects.filter(is_superuser=True).first()
                    if not created_by:
                        created_by = User.objects.first()
                
                if created_by:
                    case = Case.objects.create(
                        client=client,
                        title=f"Initial Consultation - {client.name}",
                        description=f"Initial case consultation and legal assessment for {client.name}. This case was automatically created for existing client.",
                        case_type=client.case_type,
                        status='pending',
                        priority='medium',
                        created_by=created_by
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created case "{case.title}" for client: {client.name} (Case ID: {case.id})'
                        )
                    )
                    created_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Could not create case for {client.name} - no users found in system'
                        )
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would create {clients_without_cases.count()} cases for existing clients.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} cases for existing clients.'
                )
            )