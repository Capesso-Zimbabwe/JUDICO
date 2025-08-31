from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

from finance_management.models import (
    AccountsPayable, AccountsPayableLineItem, ExpenseCategory, 
    AccountingPeriod, Account
)
from client_management.models import Client


class Command(BaseCommand):
    help = 'Populate sample accounts payable data for law firms'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate sample accounts payable data...')
        
        # Get or create a user for created_by
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f'Created admin user')
        
        # Get or create an accounting period
        period, created = AccountingPeriod.objects.get_or_create(
            name='Q4 2024',
            defaults={
                'start_date': date(2024, 10, 1),
                'end_date': date(2024, 12, 31),
                'status': 'OPEN'
            }
        )
        if created:
            self.stdout.write(f'Created accounting period: {period.name}')
        
        # Get expense categories
        expense_categories = list(ExpenseCategory.objects.filter(is_active=True))
        if not expense_categories:
            self.stdout.write(self.style.ERROR('No expense categories found. Please create expense categories first.'))
            return
        
        # Define law firm specific vendors
        law_firm_vendors = [
            # Office & Administrative
            'Office Depot',
            'Staples Business Advantage',
            'Amazon Business',
            'Uline',
            'Grainger',
            
            # Legal Services & Software
            'LexisNexis',
            'Westlaw',
            'Clio Legal Practice Management',
            'MyCase',
            'PracticePanther',
            'Rocket Lawyer',
            'LegalZoom',
            
            # Technology & IT
            'Dell Technologies',
            'HP Inc.',
            'Microsoft 365',
            'Adobe Creative Suite',
            'Zoom Video Communications',
            'Slack Technologies',
            'Dropbox Business',
            'Google Workspace',
            
            # Professional Services
            'Deloitte',
            'PwC',
            'Ernst & Young',
            'KPMG',
            'BDO USA',
            
            # Insurance & Compliance
            'The Hartford',
            'Travelers Insurance',
            'Chubb Group',
            'AIG',
            'Liberty Mutual',
            
            # Marketing & Business Development
            'LinkedIn Premium',
            'Martindale-Hubbell',
            'Super Lawyers',
            'Avvo',
            'FindLaw',
            
            # Court & Legal Services
            'CourtCall',
            'One Legal',
            'ServeNow',
            'ABC Legal Services',
            'Process Server Network',
            
            # Continuing Education
            'Practising Law Institute',
            'American Bar Association',
            'State Bar Associations',
            'Law Practice Management Section',
            'Legal Marketing Association',
            
            # Office & Facilities
            'WeWork',
            'Regus',
            'Servcorp',
            'Office Evolution',
            'Premier Workspaces',
            
            # Utilities & Services
            'Comcast Business',
            'Verizon Business',
            'AT&T Business',
            'Pacific Gas & Electric',
            'Southern California Edison'
        ]
        
        # Define sample invoice descriptions for law firms
        invoice_descriptions = [
            # Legal Research & Software
            'Annual subscription to legal research database',
            'Practice management software license renewal',
            'Document management system subscription',
            'Legal forms and templates library access',
            'Case law research tools and updates',
            
            # Office Supplies & Equipment
            'Office supplies and stationery for Q4',
            'Computer equipment and accessories',
            'Printing and copying supplies',
            'Filing cabinets and office furniture',
            'Office equipment maintenance services',
            
            # Professional Services
            'Accounting and bookkeeping services',
            'IT consulting and support services',
            'Legal marketing and SEO services',
            'Professional liability insurance premium',
            'Business insurance renewal',
            
            # Technology & Software
            'Microsoft 365 business subscription',
            'Adobe Creative Suite license renewal',
            'Cloud storage and backup services',
            'Video conferencing platform subscription',
            'Project management software license',
            
            # Marketing & Business Development
            'Professional directory listings',
            'Website hosting and maintenance',
            'Online advertising campaign',
            'Business development consulting',
            'Professional networking memberships',
            
            # Continuing Education
            'CLE course registration and materials',
            'Bar association membership dues',
            'Professional conference registration',
            'Legal education materials and books',
            'Professional development workshops',
            
            # Court & Legal Services
            'Court filing fees and services',
            'Process serving fees',
            'Expert witness consultation',
            'Court reporting services',
            'Legal document preparation',
            
            # Travel & Entertainment
            'Client meeting travel expenses',
            'Conference attendance costs',
            'Business development travel',
            'Client entertainment expenses',
            'Professional networking events'
        ]
        
        # Create sample accounts payable entries
        payables_created = 0
        
        for i in range(25):  # Create 25 sample payables
            # Random vendor
            vendor = random.choice(law_firm_vendors)
            
            # Random expense category
            expense_category = random.choice(expense_categories)
            
            # Generate invoice dates (within last 6 months)
            invoice_date = date.today() - timedelta(days=random.randint(0, 180))
            
            # Payment terms and due dates
            payment_terms = random.choice(['NET_15', 'NET_30', 'NET_45', 'NET_60'])
            if payment_terms == 'NET_15':
                due_date = invoice_date + timedelta(days=15)
            elif payment_terms == 'NET_30':
                due_date = invoice_date + timedelta(days=30)
            elif payment_terms == 'NET_45':
                due_date = invoice_date + timedelta(days=45)
            else:  # NET_60
                due_date = invoice_date + timedelta(days=60)
            
            # Generate realistic amounts
            subtotal = Decimal(str(random.randint(100, 5000) + random.random() * 100).split('.')[0] + '.' + str(random.randint(0, 99)).zfill(2))
            tax_rate = Decimal('0.085')  # 8.5% tax rate
            tax_amount = (subtotal * tax_rate).quantize(Decimal('0.01'))
            total_amount = subtotal + tax_amount
            
            # Status distribution (more realistic for law firms)
            status_weights = {
                'DRAFT': 0.1,
                'PENDING_APPROVAL': 0.2,
                'APPROVED': 0.3,
                'PARTIALLY_PAID': 0.15,
                'PAID': 0.2,
                'OVERDUE': 0.05
            }
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values())
            )[0]
            
            # Amount paid based on status
            if status == 'PAID':
                amount_paid = total_amount
                balance_due = Decimal('0.00')
            elif status == 'PARTIALLY_PAID':
                amount_paid = total_amount * Decimal(str(random.uniform(0.3, 0.7)))
                balance_due = total_amount - amount_paid
            else:
                amount_paid = Decimal('0.00')
                balance_due = total_amount
            
            # Check if overdue
            if due_date < date.today() and status not in ['PAID', 'PARTIALLY_PAID']:
                status = 'OVERDUE'
            
            # Create the accounts payable entry
            payable = AccountsPayable.objects.create(
                vendor=vendor,
                vendor_invoice_number=f"INV-{random.randint(10000, 99999)}",
                invoice_date=invoice_date,
                due_date=due_date,
                payment_terms=payment_terms,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                amount_paid=amount_paid,
                balance_due=balance_due,
                status=status,
                expense_category=expense_category,
                period=period,
                description=random.choice(invoice_descriptions),
                notes=f"Sample accounts payable entry for {vendor}",
                created_by=user,
                is_recurring=random.choice([True, False]),
                recurring_frequency=random.choice(['monthly', 'quarterly', 'annually']) if random.choice([True, False]) else ''
            )
            
            # Create line items (1-3 items per payable)
            num_line_items = random.randint(1, 3)
            for j in range(num_line_items):
                line_description = random.choice([
                    'Professional services',
                    'Software license',
                    'Office supplies',
                    'Consulting fees',
                    'Insurance premium',
                    'Membership dues',
                    'Training materials',
                    'Equipment rental',
                    'Maintenance services',
                    'Subscription fees'
                ])
                
                quantity = Decimal(str(random.randint(1, 5)))
                unit_price = (subtotal / num_line_items / quantity).quantize(Decimal('0.01'))
                line_total = (quantity * unit_price).quantize(Decimal('0.01'))
                
                # Get a random expense account for the line item
                expense_accounts = Account.objects.filter(account_type='EXPENSE', status='ACTIVE')
                if expense_accounts.exists():
                    expense_account = random.choice(expense_accounts)
                else:
                    expense_account = None
                
                AccountsPayableLineItem.objects.create(
                    payable=payable,
                    description=line_description,
                    quantity=quantity,
                    unit_price=unit_price,
                    tax_rate=Decimal('0.085'),  # 8.5% tax rate
                    line_total=line_total,
                    expense_account=expense_account
                )
            
            payables_created += 1
            self.stdout.write(f'Created payable: {payable.vendor} - ${payable.total_amount} ({payable.status})')
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {payables_created} sample accounts payable entries!'))
        
        # Summary statistics
        total_amount = sum(p.total_amount for p in AccountsPayable.objects.all())
        total_balance = sum(p.balance_due for p in AccountsPayable.objects.all())
        overdue_count = AccountsPayable.objects.filter(status='OVERDUE').count()
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'- Total Payables: {payables_created}')
        self.stdout.write(f'- Total Amount: ${total_amount:,.2f}')
        self.stdout.write(f'- Balance Due: ${total_balance:,.2f}')
        self.stdout.write(f'- Overdue: {overdue_count}')
