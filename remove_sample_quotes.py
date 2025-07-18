import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

# Import the Quote model after Django setup
from quotes.models import Quote

def remove_sample_quotes():
    # Path to sample quotes file
    sample_quotes_path = os.path.join('quotes', 'sample_quotes.txt')
    
    # Read sample quotes
    sample_quotes = []
    with open(sample_quotes_path, 'r') as f:
        sample_quotes = [line.strip() for line in f.readlines()]
    
    # Extract quote texts from sample quotes
    sample_quote_texts = []
    for quote in sample_quotes:
        if ' - ' in quote:
            text = quote.rsplit(' - ', 1)[0]
            sample_quote_texts.append(text)
        else:
            sample_quote_texts.append(quote)
    
    # Count quotes before deletion
    total_before = Quote.objects.count()
    print(f"Total quotes before: {total_before}")
    
    # Find and delete sample quotes
    deleted_count = 0
    for text in sample_quote_texts:
        # Find quotes with this text
        quotes = Quote.objects.filter(text=text)
        # If there are multiple copies, keep one and delete the rest
        if quotes.count() > 1:
            # Keep the first one
            keep_quote = quotes.first()
            # Delete the rest
            for quote in quotes[1:]:
                quote.delete()
                deleted_count += 1
    
    # Count quotes after deletion
    total_after = Quote.objects.count()
    print(f"Deleted {deleted_count} duplicate sample quotes")
    print(f"Total quotes after: {total_after}")

if __name__ == "__main__":
    remove_sample_quotes()