from django.test import TestCase, RequestFactory
from django.utils import timezone
from datetime import timedelta
from .models import Quote
from .context_processors import daily_quote


class QuoteModelTests(TestCase):
    def setUp(self):
        # Create test quotes
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Quote for today
        Quote.objects.create(
            text="Today's quote",
            author="Today's Author",
            display_date=today,
            is_active=True
        )
        
        # Quote for yesterday
        Quote.objects.create(
            text="Yesterday's quote",
            author="Yesterday's Author",
            display_date=yesterday,
            is_active=True
        )
        
        # Quote for tomorrow
        Quote.objects.create(
            text="Tomorrow's quote",
            author="Tomorrow's Author",
            display_date=tomorrow,
            is_active=True
        )
        
        # Inactive quote
        Quote.objects.create(
            text="Inactive quote",
            author="Inactive Author",
            display_date=today,
            is_active=False
        )
    
    def test_get_quote_for_today(self):
        """Test that get_quote_for_today returns the correct quote"""
        quote = Quote.get_quote_for_today()
        self.assertIsNotNone(quote)
        self.assertEqual(quote.text, "Today's quote")
        self.assertEqual(quote.author, "Today's Author")
    
    def test_get_quote_for_today_fallback(self):
        """Test that get_quote_for_today falls back to a random quote when no quote exists for today"""
        # Delete today's quote
        Quote.objects.filter(display_date=timezone.now().date()).delete()
        
        # Should fall back to a random quote
        quote = Quote.get_quote_for_today()
        self.assertIsNotNone(quote)
        self.assertTrue(
            quote.text in ["Yesterday's quote", "Tomorrow's quote"]
        )
    
    def test_inactive_quotes_excluded(self):
        """Test that inactive quotes are excluded"""
        # Set all active quotes to inactive except the inactive one
        Quote.objects.filter(is_active=True).update(is_active=False)
        Quote.objects.filter(text="Inactive quote").update(is_active=True)
        
        quote = Quote.get_quote_for_today()
        self.assertEqual(quote.text, "Inactive quote")


class ContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create a quote for today
        today = timezone.now().date()
        Quote.objects.create(
            text="Test quote for context processor",
            author="Test Author",
            display_date=today,
            is_active=True
        )
    
    def test_daily_quote_context_processor_first_request(self):
        """Test that the daily_quote context processor adds the quote to the context on first request"""
        request = self.factory.get('/')
        request.session = {}
        
        context = daily_quote(request)
        
        self.assertIn('daily_quote', context)
        self.assertIsNotNone(context['daily_quote'])
        self.assertEqual(
            context['daily_quote'].text,
            "Test quote for context processor"
        )
        
        # Check that the quote was stored in the session
        self.assertIn('daily_quote', request.session)
        self.assertIn('quote_date', request.session)
    
    def test_daily_quote_context_processor_from_session(self):
        """Test that the daily_quote context processor uses the quote from the session"""
        from datetime import datetime
        
        request = self.factory.get('/')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Simulate a quote already in the session
        request.session = {
            'daily_quote': {
                'id': 999,
                'text': 'Session quote',
                'author': 'Session Author',
                'display_date': None
            },
            'quote_date': today
        }
        
        context = daily_quote(request)
        
        self.assertIn('daily_quote', context)
        self.assertIsNotNone(context['daily_quote'])
        self.assertEqual(context['daily_quote'].text, 'Session quote')
        self.assertEqual(context['daily_quote'].author, 'Session Author')
        
    def test_daily_quote_context_processor_expired_session(self):
        """Test that the context processor gets a new quote when the session quote is expired"""
        from datetime import datetime
        
        request = self.factory.get('/')
        yesterday = '2023-01-01'  # Use a fixed date in the past
        
        # Simulate an expired quote in the session
        request.session = {
            'daily_quote': {
                'id': 999,
                'text': 'Old session quote',
                'author': 'Old session Author',
                'display_date': None
            },
            'quote_date': yesterday
        }
        
        context = daily_quote(request)
        
        self.assertIn('daily_quote', context)
        self.assertIsNotNone(context['daily_quote'])
        self.assertEqual(
            context['daily_quote'].text,
            "Test quote for context processor"
        )
        
        # Check that the quote was updated in the session
        self.assertIn('daily_quote', request.session)
        self.assertIn('quote_date', request.session)
        self.assertNotEqual(request.session['quote_date'], yesterday)
