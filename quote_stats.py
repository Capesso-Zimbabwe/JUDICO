from quotes.models import Quote

def print_quote_stats():
    total_quotes = Quote.objects.count()
    unknown_quotes = Quote.objects.filter(author__iexact='unknown').count()
    known_quotes = Quote.objects.exclude(author__iexact='unknown').count()
    
    print(f'Total quotes: {total_quotes}')
    print(f'Quotes with known author: {known_quotes}')
    print(f'Quotes with unknown author: {unknown_quotes}')
    
    print('\nSample quotes with known authors:')
    for quote in Quote.objects.exclude(author__iexact='unknown').order_by('?')[:5]:
        print(f'- "{quote.text}" - {quote.author}')

if __name__ == '__main__':
    print_quote_stats()