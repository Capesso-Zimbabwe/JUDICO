from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
from finance_management.models import (
    Invoice, InvoiceItem, Payment, Expense, ExpenseCategory,
    Client, AccountsPayable, AccountsPayableLineItem
)
from client_management.models import Client as ClientModel

class Command(BaseCommand):
    help = 'Populate finance system with sample data for dashboard testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample finance data...')
        
        # Create sample clients if they don't exist
        clients = []
        client_names = [
            'ABC Corporation', 'XYZ Limited', 'Tech Solutions Inc', 
            'Legal Partners LLC', 'Global Enterprises', 'Startup Ventures',
            'Consulting Group', 'Digital Services Co', 'Innovation Labs',
            'Strategic Partners'
        ]
        
        for name in client_names:
            client, created = ClientModel.objects.get_or_create(
                name=name,
                defaults={
                    'email': f'{name.lower().replace(" ", ".")}@example.com',
                    'phone': f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'address': f'{random.randint(100, 9999)} Main St, City, State {random.randint(10000, 99999)}'
                }
            )
            clients.append(client)
            if created:
                self.stdout.write(f'Created client: {name}')
        
        # Create sample invoices and payments
        self.create_sample_invoices_and_payments(clients)
        
        # Create sample expenses
        self.create_sample_expenses()
        
        # Create sample accounts payable
        self.create_sample_accounts_payable()
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample finance data!'))

    def create_sample_invoices_and_payments(self, clients):
        # Sample invoice data
        invoice_data = [
            {'amount': 5000, 'status': 'PAID', 'days_ago': 30},
            {'amount': 8000, 'status': 'PAID', 'days_ago': 25},
            {'amount': 12000, 'status': 'PAID', 'days_ago': 20},
            {'amount': 7000, 'status': 'PAID', 'days_ago': 15},
            {'amount': 10000, 'status': 'PAID', 'days_ago': 10},
            {'amount': 15000, 'status': 'PAID', 'days_ago': 5},
            {'amount': 9000, 'status': 'SENT', 'days_ago': 3},
            {'amount': 11000, 'status': 'SENT', 'days_ago': 1},
            {'amount': 6000, 'status': 'OVERDUE', 'days_ago': 45},
            {'amount': 13000, 'status': 'OVERDUE', 'days_ago': 60},
            {'amount': 4000, 'status': 'DRAFT', 'days_ago': 0},
            {'amount': 7500, 'status': 'DRAFT', 'days_ago': 0},
        ]
        
        payment_methods = ['BANK_TRANSFER', 'CREDIT_CARD', 'CASH', 'CHECK', 'ONLINE_PAYMENT']
        
        for i, data in enumerate(invoice_data):
            # Create invoice
            issue_date = timezone.now() - timedelta(days=data['days_ago'])
            due_date = issue_date + timedelta(days=30)
            
            invoice = Invoice.objects.create(
                invoice_number=f'INV-{timezone.now().year}-{str(i+1).zfill(4)}',
                client=random.choice(clients),
                issue_date=issue_date,
                due_date=due_date,
                status=data['status'],
                subtotal=data['amount'],
                tax=data['amount'] * Decimal('0.1'),  # 10% tax
                total=data['amount'] * Decimal('1.1'),
                notes=f'Sample invoice for services rendered'
            )
            
            # Create invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                description='Professional Services',
                quantity=1,
                unit_price=data['amount'],
                amount=data['amount']
            )
            
            # Create payment if invoice is paid
            if data['status'] == 'PAID':
                payment_date = issue_date + timedelta(days=random.randint(1, 25))
                Payment.objects.create(
                    invoice=invoice,
                    amount=data['amount'] * Decimal('1.1'),
                    payment_date=payment_date,
                    payment_method=random.choice(payment_methods),
                    reference_number=f'REF-{random.randint(10000, 99999)}',
                    notes='Sample payment'
                )
            
            self.stdout.write(f'Created invoice: {invoice.invoice_number} - ${data["amount"]} - {data["status"]}')

    def create_sample_expenses(self):
        # Create expense accounts first
        expense_accounts = {
            'OFFICE_SUPPLIES': 'Office Supplies Expense',
            'UTILITIES': 'Utilities Expense', 
            'RENT': 'Rent Expense',
            'TRAVEL': 'Travel Expense',
            'PROFESSIONAL_FEES': 'Professional Fees Expense',
            'MARKETING': 'Marketing Expense',
            'OTHER': 'Other Expenses'
        }
        
        # Create expense categories if they don't exist
        categories = [
            'OFFICE_SUPPLIES', 'UTILITIES', 'RENT', 'TRAVEL', 
            'PROFESSIONAL_FEES', 'MARKETING', 'OTHER'
        ]
        
        for i, category_name in enumerate(categories):
            # Create or get the expense account
            account, created = Account.objects.get_or_create(
                code=f'5000{i+1}',
                defaults={
                    'name': expense_accounts[category_name],
                    'account_type': 'EXPENSE',
                    'account_category': 'OPERATING_EXPENSE',
                    'normal_balance': 'DEBIT',
                    'description': f'Account for {expense_accounts[category_name]}'
                }
            )
            
            # Create or get the expense category
            category, created = ExpenseCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': f'Sample {category_name.lower().replace("_", " ")} category',
                    'account': account
                }
            )
        
        # Sample expense data
        expense_data = [
            {'amount': 500, 'category': 'OFFICE_SUPPLIES', 'status': 'APPROVED', 'days_ago': 30},
            {'amount': 800, 'category': 'UTILITIES', 'status': 'APPROVED', 'days_ago': 25},
            {'amount': 2000, 'category': 'RENT', 'status': 'APPROVED', 'days_ago': 20},
            {'amount': 1200, 'category': 'TRAVEL', 'status': 'APPROVED', 'days_ago': 15},
            {'amount': 3000, 'category': 'PROFESSIONAL_FEES', 'status': 'APPROVED', 'days_ago': 10},
            {'amount': 1500, 'category': 'MARKETING', 'status': 'APPROVED', 'days_ago': 5},
            {'amount': 900, 'category': 'OFFICE_SUPPLIES', 'status': 'PENDING', 'days_ago': 3},
            {'amount': 1100, 'category': 'UTILITIES', 'status': 'PENDING', 'days_ago': 1},
            {'amount': 600, 'category': 'OTHER', 'status': 'PENDING', 'days_ago': 0},
        ]
        
        for i, data in enumerate(expense_data):
            expense_date = timezone.now() - timedelta(days=data['days_ago'])
            
            # Get or create a user for created_by field
            from django.contrib.auth.models import User
            user, created = User.objects.get_or_create(
                username='admin',
                defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
            )
            if created:
                user.set_password('admin123')
                user.save()
            
            expense = Expense.objects.create(
                title=f'Sample {data["category"].lower().replace("_", " ")} expense',
                description=f'Sample expense for {data["category"].lower().replace("_", " ")}',
                expense_date=expense_date,
                expense_category=ExpenseCategory.objects.get(name=data['category']),
                total_amount=data['amount'],
                net_amount=data['amount'],
                status=data['status'],
                vendor=f'Sample Vendor {i+1}',
                created_by=user
            )
            
            self.stdout.write(f'Created expense: {expense.title} - ${data["amount"]} - {data["status"]}')

    def create_sample_accounts_payable(self):
        # Sample accounts payable data
        ap_data = [
            {'amount': 2500, 'status': 'PENDING_APPROVAL', 'days_ago': 5},
            {'amount': 1800, 'status': 'APPROVED', 'days_ago': 10},
            {'amount': 3200, 'status': 'PARTIALLY_PAID', 'days_ago': 15},
            {'amount': 1500, 'status': 'PAID', 'days_ago': 20},
            {'amount': 2100, 'status': 'PENDING_APPROVAL', 'days_ago': 2},
        ]
        
        vendors = ['Office Supplies Co', 'Utility Services Inc', 'Travel Agency Ltd', 
                  'Marketing Partners', 'Legal Services Corp']
        
        for i, data in enumerate(ap_data):
            invoice_date = timezone.now() - timedelta(days=data['days_ago'])
            due_date = invoice_date + timedelta(days=30)
            
            ap = AccountsPayable.objects.create(
                vendor=random.choice(vendors),
                vendor_invoice_number=f'VINV-{random.randint(10000, 99999)}',
                invoice_date=invoice_date,
                due_date=due_date,
                subtotal=data['amount'],
                total_amount=data['amount'],
                status=data['status'],
                description=f'Sample accounts payable for {random.choice(vendors)}',
                created_by=user
            )
            
            # Create line item
            AccountsPayableLineItem.objects.create(
                accounts_payable=ap,
                description='Sample line item',
                quantity=1,
                unit_price=data['amount'],
                amount=data['amount']
            )
            
            self.stdout.write(f'Created AP: {ap.reference_number} - ${data["amount"]} - {data["status"]}')