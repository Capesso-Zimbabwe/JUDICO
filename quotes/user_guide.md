# Daily Quote Feature - User Guide

## Overview

The JUDICO application now includes a daily quote feature that displays inspirational quotes throughout the year. Each day, a different quote will appear at the top of the page across all portals in the application.

## Features

- **Daily Rotation**: A new quote is displayed each day
- **Inspirational Content**: Quotes from famous thinkers, leaders, and visionaries
- **Consistent Display**: The same quote appears across all portals on a given day

## Where to Find Quotes

The daily quote appears at the top of the main content area on all pages throughout the JUDICO application, including:

- Client Portal
- Lawyer Portal
- Admin Portal
- All management sections

## Example

Here's an example of what you might see:

> "The future belongs to those who believe in the beauty of their dreams." - Eleanor Roosevelt

## For Administrators

If you have administrator access, you can manage the quotes through the Django admin interface:

1. Navigate to the admin interface
2. Go to the "Quotes" section
3. From here, you can:
   - Add new quotes
   - Edit existing quotes
   - Set specific display dates
   - Activate or deactivate quotes

## Adding Your Own Quotes

Administrators can add quotes in two ways:

### Through the Admin Interface

1. Go to the admin interface
2. Click "Add Quote"
3. Enter the quote text and author
4. Set a display date
5. Mark as active
6. Save

### By Importing from a Word Document

1. Create a Word document with one quote per paragraph
2. For quotes with authors, use the format: "Quote text - Author name"
3. Run the import command:
   ```
   python manage.py import_quotes path/to/your/quotes.docx
   ```

## Feedback

If you have suggestions for quotes or feedback about this feature, please contact your system administrator.