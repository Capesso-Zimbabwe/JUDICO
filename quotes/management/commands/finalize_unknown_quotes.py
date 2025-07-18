from django.core.management.base import BaseCommand
from quotes.models import Quote

class Command(BaseCommand):
    help = 'Finalize remaining quotes with unknown authors by setting them to Anonymous'

    def handle(self, *args, **options):
        # Get all quotes with unknown author
        unknown_quotes = Quote.objects.filter(author__iexact='unknown')
        count = unknown_quotes.count()
        self.stdout.write(f'Found {count} quotes with unknown author')
        
        # Process each quote
        updated_count = 0
        for quote in unknown_quotes:
            # Check if it's a section header
            if quote.text.startswith('🔹') or quote.text == 'JUDICO Daily Quotes' or quote.text.startswith('This document contains'):
                # Set author to 'Section Header'
                quote.author = 'Section Header'
            else:
                # Set author to 'Anonymous'
                quote.author = 'Anonymous'
            
            # Save the quote
            quote.save()
            updated_count += 1
            self.stdout.write(f'Updated quote ID {quote.id}: "{quote.text}" - {quote.author}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} quotes'))