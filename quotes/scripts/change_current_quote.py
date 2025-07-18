"""Script to change the current quote.

This script automatically changes the current quote without requiring user input.
It will select a random quote from the database and set it as today's quote.

To run this script, use Django's runscript command:
    python manage.py runscript change_current_quote
"""

import sys
from datetime import datetime
from django.utils import timezone

def run():
    # This is needed to set up Django environment
    print("Setting up Django environment...")

    try:
        # Import the Quote model
        from quotes.models import Quote
        
        # Display the current quote
        print("\n1. Current quote for today:")
        today_quote = Quote.get_quote_for_today()
        if today_quote:
            print(f'ID: {today_quote.id}')
            print(f'Text: "{today_quote.text}"')
            print(f'Author: {today_quote.author}')
            print(f'Display date: {today_quote.display_date}')
        else:
            print("No quote found for today.")
        
        # Get a random quote that is different from the current one
        today = timezone.now().date()
        
        # Get a random quote that is different from the current one
        if today_quote:
            selected_quote = Quote.objects.filter(is_active=True).exclude(id=today_quote.id).order_by('?').first()
        else:
            selected_quote = Quote.objects.filter(is_active=True).order_by('?').first()
        
        if selected_quote:
            print(f"\nSelected a random quote (ID: {selected_quote.id})")
            
            # Clear any existing quotes set for today
            Quote.objects.filter(display_date=today).update(display_date=None)
            
            # Set the selected quote for today
            selected_quote.display_date = today
            selected_quote.save()
            
            print("\nToday's quote has been updated:")
            print(f'Text: "{selected_quote.text}"')
            print(f'Author: {selected_quote.author}')
        else:
            print("\nNo active quotes found to select from.")
        
        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're running this script using 'python manage.py runscript change_current_quote'")