from django.core.management.base import BaseCommand
from django.db import transaction
from finance_management.models import AccountingPeriod, JournalEntry

class Command(BaseCommand):
    help = 'Clear all existing accounting periods (use with caution - this will remove all periods)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to clear all periods'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will delete ALL accounting periods and any associated data.\n'
                    'Use --confirm to proceed.'
                )
            )
            return

        # Check if there are any journal entries
        entry_count = JournalEntry.objects.count()
        if entry_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'Cannot clear periods: {entry_count} journal entries exist.\n'
                    'Please delete all journal entries first, or use the admin interface to manage periods manually.'
                )
            )
            return

        with transaction.atomic():
            # Delete all periods
            deleted_count = AccountingPeriod.objects.count()
            AccountingPeriod.objects.all().delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleared {deleted_count} accounting periods.\n'
                    'You can now create periods manually as needed.'
                )
            )
            self.stdout.write(
                'To create periods manually:\n'
                '1. Use the Django admin interface: /admin/finance_management/accountingperiod/\n'
                '2. Or use the create_periods command: python manage.py create_periods YEAR\n'
                '3. Or create them through the application interface'
            )
