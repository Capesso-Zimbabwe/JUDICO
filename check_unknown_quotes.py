from quotes.models import Quote

# Count quotes
total_quotes = Quote.objects.count()
unknown_quotes = Quote.objects.filter(author__iexact='unknown').count()
known_quotes = Quote.objects.exclude(author__iexact='unknown').count()

print(f'Total quotes: {total_quotes}')
print(f'Quotes with known author: {known_quotes}')
print(f'Quotes with unknown author: {unknown_quotes}')

print('\nRemaining quotes with unknown author:')
for quote in Quote.objects.filter(author__iexact='unknown'):
    print(f'ID: {quote.id}, Text: "{quote.text}"')