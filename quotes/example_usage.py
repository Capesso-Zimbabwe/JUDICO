"""Example script showing how to use the quotes app programmatically.

This script demonstrates how to:
1. Get the quote for today
2. Get a random quote
3. Create a new quote
4. Update an existing quote

To run this script, use Django's shell:
    python manage.py shell < quotes/example_usage.py
"""

import sys
from datetime import datetime, timedelta
from django.utils import timezone

# This is needed to set up Django environment
print("Setting up Django environment...")

try:
    # Try to import the Quote model
    from quotes.models import Quote
    
    # Example 1: Get today's quote
    print("\n1. Today's quote:")
    today_quote = Quote.get_quote_for_today()
    if today_quote:
        print(f'"{today_quote.text}" - {today_quote.author}')
    else:
        print("No quote found for today.")
    
    # Example 2: Get a random quote
    print("\n2. Random quote:")
    random_quote = Quote.objects.filter(is_active=True).order_by('?').first()
    if random_quote:
        print(f'"{random_quote.text}" - {random_quote.author}')
    else:
        print("No active quotes found.")
    
    # Example 3: Create a new quote
    print("\n3. Creating a new quote:")
    tomorrow = timezone.now().date() + timedelta(days=1)
    new_quote = Quote.objects.create(
        text="The best way to predict the future is to create it.",
        author="Abraham Lincoln",
        display_date=tomorrow,
        is_active=True
    )
    print(f"Created quote ID {new_quote.id} for {tomorrow}")
    
    # Example 4: Update an existing quote
    print("\n4. Updating a quote:")
    if new_quote:
        new_quote.text = "The best way to predict the future is to invent it."
        new_quote.author = "Alan Kay"
        new_quote.save()
        print(f"Updated quote ID {new_quote.id}:")
        print(f'"{new_quote.text}" - {new_quote.author}')
    
    print("\nDone!")

except Exception as e:
    print(f"Error: {e}")
    print("Make sure you're running this script using 'python manage.py shell < quotes/example_usage.py'")
    sys.exit(1)