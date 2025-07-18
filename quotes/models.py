from django.db import models
from django.utils import timezone

class Quote(models.Model):
    """Model for storing daily quotes"""
    text = models.TextField(help_text="The quote text")
    author = models.CharField(max_length=255, blank=True, null=True, help_text="Author of the quote")
    display_date = models.DateField(null=True, blank=True, help_text="Specific date to display this quote (optional)")
    is_active = models.BooleanField(default=True, help_text="Whether this quote is active and can be displayed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_date', 'created_at']
        verbose_name = 'Quote'
        verbose_name_plural = 'Quotes'
    
    def __str__(self):
        return f"{self.text[:50]}... - {self.author or 'Unknown'}"
    
    @classmethod
    def get_quote_for_today(cls):
        """Returns a quote for today's date or a random active quote if none is specifically assigned"""
        today = timezone.now().date()
        # First try to find a quote specifically for today
        today_quote = cls.objects.filter(display_date=today, is_active=True).first()
        if today_quote:
            return today_quote
        
        # If no quote is assigned for today, get a random active quote
        import random
        active_quotes = list(cls.objects.filter(is_active=True))
        if active_quotes:
            return random.choice(active_quotes)
        
        return None
    
    @classmethod
    def get_random_quote(cls):
        """Returns a random active quote from the database"""
        import random
        active_quotes = list(cls.objects.filter(is_active=True))
        if active_quotes:
            return random.choice(active_quotes)
        
        return None
