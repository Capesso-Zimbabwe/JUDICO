import os
import sys
import django
import random
from datetime import datetime, timedelta
from docx import Document

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JUDICO_HUB.settings')
django.setup()

# Import the Quote model after Django setup
from quotes.models import Quote

def import_quotes_from_docx(docx_path):
    """
    Import quotes from a Word document into the database.
    
    The Word document should have each quote on a separate paragraph.
    If the quote has an author, it should be in the format: "Quote text - Author name"
    """
    try:
        # Load the Word document
        doc = Document(docx_path)
        
        # Get all paragraphs from the document
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        # Count of quotes imported
        imported_count = 0
        
        # Generate dates for the whole year
        today = datetime.now().date()
        start_date = today
        dates = []
        
        # Create a list of dates for the next 365 days
        for i in range(365):
            dates.append(start_date + timedelta(days=i))
        
        # Shuffle the dates to randomly assign them to quotes
        random.shuffle(dates)
        
        # Process each paragraph as a quote
        for i, paragraph in enumerate(paragraphs):
            # Skip empty paragraphs
            if not paragraph:
                continue
                
            # Check if the quote has an author (format: "Quote - Author")
            if ' - ' in paragraph:
                text, author = paragraph.rsplit(' - ', 1)
            else:
                text = paragraph
                author = None
            
            # Assign a date if we have enough dates
            display_date = dates[i] if i < len(dates) else None
            
            # Create the quote
            Quote.objects.create(
                text=text,
                author=author,
                display_date=display_date,
                is_active=True
            )
            
            imported_count += 1
        
        return f"Successfully imported {imported_count} quotes from {docx_path}"
    
    except Exception as e:
        return f"Error importing quotes: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_quotes.py <path_to_docx_file>")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    result = import_quotes_from_docx(docx_path)
    print(result)