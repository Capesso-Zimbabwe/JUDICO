from django.core.management.base import BaseCommand
from document_repository.models import DocumentCategory

class Command(BaseCommand):
    help = 'Populate default document categories'
    
    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Legal Documents',
                'description': 'Legal contracts, agreements, and court documents',
                'icon': 'fas fa-gavel',
                'color': 'blue'
            },
            {
                'name': 'Contracts',
                'description': 'Client contracts and service agreements',
                'icon': 'fas fa-file-contract',
                'color': 'green'
            },
            {
                'name': 'Financial',
                'description': 'Financial documents, invoices, and receipts',
                'icon': 'fas fa-dollar-sign',
                'color': 'yellow'
            },
            {
                'name': 'Correspondence',
                'description': 'Letters, emails, and communication records',
                'icon': 'fas fa-envelope',
                'color': 'purple'
            },
            {
                'name': 'Reports',
                'description': 'Case reports, research, and analysis documents',
                'icon': 'fas fa-chart-bar',
                'color': 'red'
            },
            {
                'name': 'Client Files',
                'description': 'Client-specific documents and case files',
                'icon': 'fas fa-user-tie',
                'color': 'indigo'
            },
            {
                'name': 'Administrative',
                'description': 'Internal administrative documents and policies',
                'icon': 'fas fa-cogs',
                'color': 'gray'
            },
            {
                'name': 'Templates',
                'description': 'Document templates and forms',
                'icon': 'fas fa-file-alt',
                'color': 'teal'
            }
        ]
        
        created_count = 0
        for category_data in categories:
            category, created = DocumentCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'icon': category_data['icon'],
                    'color': category_data['color']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCompleted! Created {created_count} new categories.')
        )