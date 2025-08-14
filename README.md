# JUDICO HUB - Comprehensive Legal Practice Management System

## Overview

JUDICO HUB is an integrated legal practice management system designed to streamline and automate various aspects of law firm operations. It provides a comprehensive suite of modules that handle everything from client management to financial operations, compliance, and document management.

## Key Features

### Client Management
- Client profiles and information management
- Case tracking and management
- Court diary and scheduling
- Client portal for communication and document sharing

### Task Management
- Task assignment and tracking
- Deadline management
- Workflow automation
- Progress tracking and reporting

### Finance Management
- Invoice generation and management
- Payment tracking
- Expense management
- Financial reporting
- Account management

### HR Management
- Staff profiles and information
- Leave management
- Performance reviews
- Time sheets tracking
- Lawyer management

### Document Repository
- Secure document storage
- Document versioning
- Document templates
- Document sharing and collaboration

### Contract Management
- Contract creation and templates
- Contract lifecycle management
- Signature management
- Amendment tracking
- Contract analytics and reporting

### Transaction Support
- Transaction tracking and management
- Transaction monitoring
- Transaction reporting

### Compliance & Governance
- Policy management
- Meeting management
- Compliance reporting
- Audit trails
- Regulatory calendar

### KYC & AML System
- Know Your Customer (KYC) profiles
- Anti-Money Laundering (AML) screening
- Risk assessment and scoring
- Sanctions and watchlist checking
- Compliance reporting

### Quotes Feature
- Daily rotating inspirational quotes
- Displayed across all portals
- Customizable through admin interface

## User Portals

JUDICO HUB provides different portals for different user types:

- **Admin Portal**: For system administrators to manage the entire system
- **Client Portal**: For clients to access their cases, documents, and communicate with the firm
- **Lawyer Portal**: For lawyers to manage their cases, tasks, and client interactions

## Technical Information

- Built with Django web framework
- Uses Tailwind CSS for modern, responsive UI
- Implements HTMX for dynamic interactions
- SQLite database (configurable for production environments)

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Module Setup

Some modules have specific setup scripts, such as the Quotes module:

```bash
# Windows
quotes\setup_quotes_app.bat

# PowerShell
.\quotes\setup_quotes_app.ps1
```

## Security Notice

This repository contains a development configuration. For production deployment:

- Change the SECRET_KEY in settings.py
- Set DEBUG=False
- Configure a production-ready database
- Set up proper static file serving
- Implement HTTPS