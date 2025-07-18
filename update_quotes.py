from quotes.models import Quote

def update_quotes_with_unknown_author():
    print("Starting to update quotes with 'unknown' author...")
    unknown_quotes = Quote.objects.filter(author__iexact='unknown')
    print(f"Found {unknown_quotes.count()} quotes with 'unknown' author")
    
    updated_count = 0
    for quote in unknown_quotes:
        print(f"\nProcessing quote ID {quote.id}: {quote.text[:50]}...")
        
        if ' — ' in quote.text:
            print("Found em dash separator")
            text_parts = quote.text.split(' — ')
        elif ' - ' in quote.text:
            print("Found hyphen separator")
            text_parts = quote.text.split(' - ')
        else:
            print("No separator found, skipping")
            continue
        
        if len(text_parts) > 1:
            author_part = text_parts[-1].strip()
            if author_part:
                old_author = quote.author
                quote.author = author_part
                quote.text = text_parts[0].strip()
                quote.save()
                updated_count += 1
                print(f"Updated quote ID {quote.id}: Author changed from '{old_author}' to '{author_part}'")
                print(f"New text: {quote.text}")
            else:
                print("Empty author part, skipping")
        else:
            print("No author part found after splitting, skipping")
    
    print(f"\nTotal: Updated {updated_count} quotes with extracted authors")

if __name__ == '__main__':
    update_quotes_with_unknown_author()