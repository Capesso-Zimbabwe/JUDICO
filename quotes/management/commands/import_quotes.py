import os
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from quotes.models import Quote

try:
    import docx
except ImportError:
    raise CommandError("python-docx is required. Install it using 'pip install python-docx'")


class Command(BaseCommand):
    help = 'Import quotes from a Word document into the database'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Word document containing quotes')
        parser.add_argument(
            '--clear', 
            action='store_true', 
            help='Clear existing quotes before importing'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        clear_existing = options.get('clear', False)
        
        if not os.path.exists(file_path):
            raise CommandError(f"File {file_path} does not exist")
        
        try:
            # Clear existing quotes if requested
            if clear_existing:
                Quote.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Cleared existing quotes'))
            
            # Load the document
            doc = docx.Document(file_path)
            
            # Get all paragraphs that contain text
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            
            # Generate dates for the next 365 days
            today = timezone.now().date()
            dates = [(today + timedelta(days=i)) for i in range(365)]
            
            # Shuffle dates to randomize quote display dates
            random.shuffle(dates)
            
            quotes_created = 0
            for i, paragraph in enumerate(paragraphs):
                if i >= len(dates):
                    # If we have more quotes than dates, cycle back to the beginning
                    date_index = i % len(dates)
                else:
                    date_index = i
                
                # Check if the paragraph contains an author (format: "Quote text - Author name")
                if ' - ' in paragraph:
                    text, author = paragraph.rsplit(' - ', 1)
                else:
                    text = paragraph
                    author = 'Unknown'
                
                # Create the quote
                Quote.objects.create(
                    text=text,
                    author=author,
                    display_date=dates[date_index],
                    is_active=True
                )
                quotes_created += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {quotes_created} quotes')
            )
            
        except Exception as e:
            raise CommandError(f"Error importing quotes: {str(e)}")