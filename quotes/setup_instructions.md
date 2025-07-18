# Setting Up the Daily Quote Feature

This document provides step-by-step instructions for setting up the daily quote feature in the JUDICO application.

## Prerequisites

- Python 3.6 or higher
- Django 3.2 or higher
- python-docx library (`pip install python-docx`)

## Setup Steps

### 1. Install Dependencies

```bash
pip install python-docx
```

### 2. Run Migrations

```bash
python manage.py makemigrations quotes
python manage.py migrate quotes
```

### 3. Create a Word Document with Quotes

You can either:

- Use the provided sample quotes by running:
  ```bash
  python quotes/create_sample_docx.py
  ```

- Or create your own Word document with quotes. Each quote should be on a separate line. If you want to include the author, use the format: "Quote text - Author name"

### 4. Import Quotes

```bash
python manage.py import_quotes path/to/your/quotes.docx
```

Options:
- `--clear`: Clear existing quotes before importing

### 5. Verify Setup

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Visit any page in the application. You should see the daily quote displayed above the main content area.

3. Access the Django admin interface to manage quotes:
   ```
   http://localhost:8000/admin/quotes/quote/
   ```

## Automated Setup

For Windows users, you can use the provided setup scripts:

- **Batch file**: Run `quotes\setup_quotes_app.bat`
- **PowerShell**: Run `quotes\setup_quotes_app.ps1`

These scripts will install dependencies, create a sample Word document, run migrations, and import quotes automatically.

## Customization

To customize the quote display, edit the template at:
```
quotes/templates/quotes/quote_display.html
```

## Troubleshooting

- **No quote displayed**: Make sure you have imported quotes and at least one quote is marked as active.
- **Same quote every day**: Check that you have multiple quotes with different display dates.
- **Error importing quotes**: Ensure your Word document is properly formatted and accessible.

## Additional Information

The quotes app includes:

- A database model for storing quotes
- A context processor to make quotes available in all templates
- An admin interface for managing quotes
- A management command for importing quotes from Word documents

Each quote is assigned a specific display date, ensuring a different quote is shown each day throughout the year.