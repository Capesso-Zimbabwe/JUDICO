from django.core.management.base import BaseCommand
from finance_management.models import JournalEntry
from django.db import transaction

class Command(BaseCommand):
    help = 'Clear all journal entries from the database'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                count = JournalEntry.objects.count()
                JournalEntry.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} journal entries'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
