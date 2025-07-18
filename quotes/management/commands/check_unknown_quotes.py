from django.core.management.base import BaseCommand
from quotes.models import Quote

class Command(BaseCommand):
    help = 'Check quotes with unknown authors'

    def handle(self, *args, **options):
        # Count quotes
        total_quotes = Quote.objects.count()
        unknown_quotes = Quote.objects.filter(author__iexact='unknown').count()
        known_quotes = Quote.objects.exclude(author__iexact='unknown').count()

        self.stdout.write(f'Total quotes: {total_quotes}')
        self.stdout.write(f'Quotes with known author: {known_quotes}')
        self.stdout.write(f'Quotes with unknown author: {unknown_quotes}')

        self.stdout.write('\nRemaining quotes with unknown author:')
        for quote in Quote.objects.filter(author__iexact='unknown'):
            self.stdout.write(f'ID: {quote.id}, Text: "{quote.text}"')