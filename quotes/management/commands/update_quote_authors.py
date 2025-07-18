from django.core.management.base import BaseCommand
from quotes.models import Quote
import re

class Command(BaseCommand):
    help = 'Updates quotes with "unknown" author by extracting author from text'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to update quotes with "unknown" author...'))
        unknown_quotes = Quote.objects.filter(author__iexact='unknown')
        self.stdout.write(self.style.SUCCESS(f'Found {unknown_quotes.count()} quotes with "unknown" author'))
        
        updated_count = 0
        for quote in unknown_quotes:
            self.stdout.write(f'\nProcessing quote ID {quote.id}: {quote.text[:50]}...')
            
            # Try different separator patterns
            author = None
            text = quote.text
            
            # Skip section headers or empty quotes
            if text.startswith('🔹') or text == '---':
                self.stdout.write(self.style.WARNING('Skipping section header or empty quote'))
                continue
            
            # Check for common patterns with author at the end
            patterns = [
                # Pattern 1: Text — Author
                (r'(.+)\s+—\s+(.+)', 'em dash with spaces'),
                # Pattern 2: Text - Author
                (r'(.+)\s+-\s+(.+)', 'hyphen with spaces'),
                # Pattern 3: Text – Author
                (r'(.+)\s+–\s+(.+)', 'en dash with spaces'),
                # Pattern 4: Text—Author (no spaces)
                (r'(.+)—(.+)', 'em dash without spaces'),
                # Pattern 5: Text-Author (no spaces)
                (r'(.+)-(.+)', 'hyphen without spaces'),
                # Pattern 6: Text–Author (no spaces)
                (r'(.+)–(.+)', 'en dash without spaces'),
                # Pattern 7: Text. —Author
                (r'(.+)\. —(.+)', 'period followed by em dash'),
                # Pattern 8: Text. -Author
                (r'(.+)\. -(.+)', 'period followed by hyphen'),
                # Pattern 9: Text. –Author
                (r'(.+)\. –(.+)', 'period followed by en dash'),
            ]
            
            for pattern, pattern_name in patterns:
                match = re.search(pattern, text)
                if match:
                    self.stdout.write(f'Found {pattern_name} separator')
                    text_part = match.group(1).strip()
                    author_part = match.group(2).strip()
                    
                    # Clean up text part (remove numbering and quotes)
                    text_part = re.sub(r'^\d+\.\s+', '', text_part)
                    
                    # Clean up author part
                    author_part = author_part.strip()
                    
                    if author_part:
                        author = author_part
                        text = text_part
                        break
            
            # If no match found with patterns, try to find author at the end after a period
            if not author and '.' in text:
                last_period_index = text.rindex('.')
                if last_period_index < len(text) - 1:  # Not the last character
                    potential_author = text[last_period_index + 1:].strip()
                    if potential_author and len(potential_author) > 1 and potential_author[0] in ['-', '–', '—']:
                        self.stdout.write('Found author after period')
                        author = potential_author[1:].strip()
                        text = text[:last_period_index + 1].strip()
            
            if author:
                old_author = quote.author
                # Truncate author name if it's too long (max 255 chars)
                if len(author) > 255:
                    self.stdout.write(self.style.WARNING(f'Author name too long, truncating: {author[:50]}...'))
                    author = author[:255]
                
                quote.author = author
                quote.text = text
                quote.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'Updated quote ID {quote.id}: Author changed from "{old_author}" to "{author}"'))
                self.stdout.write(f'New text: {quote.text}')
            else:
                self.stdout.write(self.style.WARNING('No author found in text, skipping'))
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal: Updated {updated_count} quotes with extracted authors'))