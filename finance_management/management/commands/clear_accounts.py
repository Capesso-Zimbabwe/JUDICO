from django.core.management.base import BaseCommand
from finance_management.models import Account, JournalEntry
from django.db import transaction

class Command(BaseCommand):
    help = 'Clear all accounts and related journal entries from the database'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # First delete all journal entries since they reference accounts
                journal_count = JournalEntry.objects.count()
                JournalEntry.objects.all().delete()
                
                # Then delete all accounts
                account_count = Account.objects.count()
                Account.objects.all().delete()
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully deleted {account_count} accounts and {journal_count} journal entries'
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
