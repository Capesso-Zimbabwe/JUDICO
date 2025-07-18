# Quotes App for JUDICO

This Django app provides a daily rotating quote system for the JUDICO application. It displays a different quote each day across all portals.

## Features

- Daily rotating quotes
- Admin interface for managing quotes
- Import quotes from Word documents
- Context processor to make quotes available in all templates

## Installation

1. Install the required dependencies:

```bash
pip install -r quotes/requirements.txt
```

2. Add 'quotes' to INSTALLED_APPS in settings.py
3. Add the context processor in settings.py:

```python
TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': [
                # ...
                'quotes.context_processors.daily_quote',
            ],
        },
    },
]
```

4. Run migrations:

```bash
python manage.py makemigrations quotes
python manage.py migrate quotes
```

## Importing Quotes from Word Document

Use the provided management command to import quotes from a Word document:

```bash
python manage.py import_quotes path/to/your/quotes.docx
```

The Word document should have each quote on a separate paragraph. If you want to include the author, use the format: "Quote text - Author name"

Options:
- `--clear`: Clear existing quotes before importing

## Usage in Templates

The quote is automatically available in all templates through the context processor. You can display it using:

```html
{% include 'quotes/quote_display.html' %}
```

Or access the quote directly:

```html
{% if daily_quote %}
    <blockquote>
        {{ daily_quote.text }}
        {% if daily_quote.author != 'Unknown' %}
            <footer>- {{ daily_quote.author }}</footer>
        {% endif %}
    </blockquote>
{% endif %}
```

## Admin Interface

Quotes can be managed through the Django admin interface. You can:
- Add, edit, or delete quotes
- Set specific display dates for quotes
- Activate or deactivate quotes