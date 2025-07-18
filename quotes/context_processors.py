import json
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
from .models import Quote

def daily_quote(request):
    """
    Context processor that adds the daily quote to the template context.
    This makes the quote available to all templates.
    
    Uses session storage to avoid database queries on every request.
    The quote is stored in the session and reused until the next day.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Check if we have a quote in the session and if it's for today
    if 'daily_quote' in request.session and request.session.get('quote_date') == today:
        # Use the quote from the session
        quote_data = request.session['daily_quote']
        return {
            'daily_quote': QuoteProxy(quote_data)
        }
    
    # No quote in session or it's from a different day, get a new one
    quote = Quote.get_random_quote()
    
    if quote:
        # Store the quote in the session
        quote_data = {
            'id': quote.id,
            'text': quote.text,
            'author': quote.author,
            'display_date': quote.display_date.isoformat() if quote.display_date else None
        }
        request.session['daily_quote'] = quote_data
        request.session['quote_date'] = today
        
        return {
            'daily_quote': quote
        }
    
    return {
        'daily_quote': None
    }


class QuoteProxy:
    """
    A proxy class to mimic the Quote model for session-stored quotes.
    This allows templates to access quote attributes in the same way
    whether the quote comes from the database or the session.
    """
    def __init__(self, data):
        self.id = data.get('id')
        self.text = data.get('text')
        self.author = data.get('author')
        self.display_date = data.get('display_date')