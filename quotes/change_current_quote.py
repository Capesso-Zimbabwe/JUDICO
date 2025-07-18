"""Script to change the current quote.

This script allows you to:
1. View the current quote
2. List 5 random quotes
3. Set a specific quote for today's date
4. Choose a random quote for today's date

To run this script, use Django's shell:
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
        
        # List 5 random quotes
        print("\n2. Five random quotes:")
        random_quotes = list(Quote.objects.all().order_by('?')[:5])
        for i, quote in enumerate(random_quotes, 1):
            print(f'{i}. ID: {quote.id}')
            print(f'   Text: "{quote.text}"')
            print(f'   Author: {quote.author}')
            print()
        
        # Ask user to select a quote or enter a quote ID
        print("\n3. Change today's quote:")
        print("Enter the number (1-5) of one of the quotes above,")
        print("or enter a specific quote ID,")
        print("or press Enter to select a random quote:")
        
        choice = input("> ")
        
        # Process the user's choice
        selected_quote = None
        today = timezone.now().date()
        
        if not choice.strip():
            # Select a random quote
            selected_quote = Quote.objects.filter(is_active=True).order_by('?').first()
            print(f"\nSelected a random quote (ID: {selected_quote.id})")
        elif choice.isdigit() and 1 <= int(choice) <= 5 and int(choice) <= len(random_quotes):
            # Select one of the displayed quotes
            selected_quote = random_quotes[int(choice) - 1]
            print(f"\nSelected quote #{choice} (ID: {selected_quote.id})")
        elif choice.isdigit():
            # Try to find a quote with the specified ID
            try:
                selected_quote = Quote.objects.get(id=int(choice))
                print(f"\nSelected quote with ID: {selected_quote.id}")
            except Quote.DoesNotExist:
                print(f"\nNo quote found with ID: {choice}")
                return
        else:
            print(f"\nInvalid choice: {choice}")
            return
        
        if selected_quote:
            # Clear any existing quotes set for today
            Quote.objects.filter(display_date=today).update(display_date=None)
            
            # Set the selected quote for today
            selected_quote.display_date = today
            selected_quote.save()
            
            print("\nToday's quote has been updated:")
            print(f'Text: "{selected_quote.text}"')
            print(f'Author: {selected_quote.author}')
        
        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're running this script using 'python manage.py runscript change_current_quote'")

if __name__ == "__main__":
    run()