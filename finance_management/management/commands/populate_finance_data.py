from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

from finance_management.models import Invoice, Payment, Expense, Account
from client_management.models import Client

class Command(BaseCommand):
    help = 'Populate sample finance data for testing'
    
    def handle(self, *args, **options):
        # Get or create a user
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user'))
        
        # Create sample clients if they don't exist
        clients_data = [
            {'name': 'ABC Corporation', 'email': 'contact@abc-corp.com', 'phone': '+1-555-0101'},
            {'name': 'XYZ Legal Services', 'email': 'info@xyz-legal.com', 'phone': '+1-555-0102'},
            {'name': 'Tech Innovations Ltd', 'email': 'hello@techinnovations.com', 'phone': '+1-555-0103'},
            {'name': 'Global Enterprises', 'email': 'contact@global-ent.com', 'phone': '+1-555-0104'},
            {'name': 'StartUp Solutions', 'email': 'team@startup-solutions.com', 'phone': '+1-555-0105'},
        ]
        
        clients = []
        for client_data in clients_data:
            client, created = Client.objects.get_or_create(
                name=client_data['name'],
                defaults={
                    'contact_person': 'Contact Person',
                    'email': client_data['email'],
                    'phone': client_data['phone'],
                    'address': f'123 Business St, City, State 12345'
                }
            )
            clients.append(client)
            if created:
                self.stdout.write(f'Created client: {client.name}')
        
        # Create sample accounts
        accounts_data = [
            {'code': '1000', 'name': 'Cash', 'account_type': 'ASSET'},
            {'code': '1100', 'name': 'Accounts Receivable', 'account_type': 'ASSET'},
            {'code': '4000', 'name': 'Legal Services Revenue', 'account_type': 'REVENUE'},
            {'code': '5000', 'name': 'Office Expenses', 'account_type': 'EXPENSE'},
        ]
        
        for account_data in accounts_data:
            account, created = Account.objects.get_or_create(
                code=account_data['code'],
                defaults={
                    'name': account_data['name'],
                    'account_type': account_data['account_type'],
                    'status': 'ACTIVE'
                }
            )
            if created:
                self.stdout.write(f'Created account: {account.name}')
        
        # Create sample invoices
        invoice_count = 0
        payment_count = 0
        
        for i in range(15):  # Create 15 invoices
            client = random.choice(clients)
            
            # Generate invoice dates
            days_ago = random.randint(1, 90)
            issue_date = timezone.now().date() - timedelta(days=days_ago)
            due_date = issue_date + timedelta(days=30)
            
            # Generate amounts
            subtotal = Decimal(str(random.randint(1000, 10000)))
            tax = subtotal * Decimal('0.1')  # 10% tax
            total = subtotal + tax
            
            # Determine status based on dates
            today = timezone.now().date()
            if due_date < today:
                status = random.choice(['PAID', 'OVERDUE'])
            else:
                status = random.choice(['DRAFT', 'SENT', 'PAID'])
            
            invoice = Invoice.objects.create(
                invoice_number=f'INV-{2024}-{str(i+1).zfill(4)}',
                client=client,
                issue_date=issue_date,
                due_date=due_date,
                status=status,
                subtotal=subtotal,
                tax=tax,
                total=total,
                notes=f'Legal services for {client.name}'
            )
            invoice_count += 1
            
            # Create payments for paid invoices
            if status == 'PAID':
                payment_date = issue_date + timedelta(days=random.randint(1, 25))
                payment_method = random.choice(['BANK_TRANSFER', 'CHECK', 'CREDIT_CARD'])
                
                Payment.objects.create(
                    invoice=invoice,
                    amount=total,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    reference_number=f'PAY-{str(payment_count+1).zfill(6)}',
                    notes=f'Payment for invoice {invoice.invoice_number}'
                )
                payment_count += 1
        
        # Create sample expenses
        expense_categories = [
            'OFFICE_SUPPLIES', 'UTILITIES', 'RENT', 'TRAVEL', 
            'PROFESSIONAL_FEES', 'MARKETING', 'OTHER'
        ]
        
        expense_titles = {
            'OFFICE_SUPPLIES': ['Office Supplies', 'Stationery', 'Printer Ink', 'Paper'],
            'UTILITIES': ['Electricity Bill', 'Internet Service', 'Phone Bill', 'Water Bill'],
            'RENT': ['Office Rent', 'Parking Space Rent'],
            'TRAVEL': ['Client Meeting Travel', 'Conference Travel', 'Business Trip'],
            'PROFESSIONAL_FEES': ['Legal Research Subscription', 'Professional Development', 'Certification Fees'],
            'MARKETING': ['Website Maintenance', 'Business Cards', 'Advertisement'],
            'OTHER': ['Miscellaneous Expense', 'Equipment Maintenance', 'Software License']
        }
        
        expense_count = 0
        for i in range(25):  # Create 25 expenses
            category = random.choice(expense_categories)
            title = random.choice(expense_titles[category])
            
            expense_date = timezone.now().date() - timedelta(days=random.randint(1, 90))
            amount = Decimal(str(random.randint(50, 2000)))
            
            Expense.objects.create(
                title=title,
                description=f'{title} for office operations',
                amount=amount,
                category=category,
                expense_date=expense_date,
                created_by=user
            )
            expense_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created:\n'
                f'- {len(clients)} clients\n'
                f'- {invoice_count} invoices\n'
                f'- {payment_count} payments\n'
                f'- {expense_count} expenses'
            )
        )