from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from finance_management.models import Account, ExpenseCategory

class Command(BaseCommand):
    help = 'Set up default expense categories for law firm accounting system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default expense categories...')
        
        # Get or create expense categories
        self.create_expense_categories()
        
        self.stdout.write(self.style.SUCCESS('Expense categories setup completed successfully!'))

    def create_expense_categories(self):
        """Create default expense categories mapped to chart of accounts"""
        
        # Define expense categories with their corresponding accounts
        categories_data = [
            # Staff & Personnel
            {
                'name': 'Partner Salaries',
                'description': 'Salaries and compensation for partners',
                'account_code': '5000'
            },
            {
                'name': 'Associate Attorney Salaries',
                'description': 'Salaries for associate attorneys',
                'account_code': '5010'
            },
            {
                'name': 'Paralegal Salaries',
                'description': 'Salaries for paralegal staff',
                'account_code': '5020'
            },
            {
                'name': 'Legal Secretary Salaries',
                'description': 'Salaries for legal secretaries',
                'account_code': '5030'
            },
            {
                'name': 'Administrative Staff Salaries',
                'description': 'Salaries for administrative staff',
                'account_code': '5040'
            },
            {
                'name': 'Employee Benefits',
                'description': 'Health insurance, retirement, and other benefits',
                'account_code': '5050'
            },
            {
                'name': 'Payroll Taxes',
                'description': 'Employer payroll taxes and contributions',
                'account_code': '5060'
            },
            
            # Office Operations
            {
                'name': 'Office Rent',
                'description': 'Office space rental and lease payments',
                'account_code': '5070'
            },
            {
                'name': 'Utilities',
                'description': 'Electricity, water, gas, and other utilities',
                'account_code': '5080'
            },
            {
                'name': 'Office Supplies',
                'description': 'General office supplies and materials',
                'account_code': '5090'
            },
            {
                'name': 'Legal Supplies',
                'description': 'Legal-specific supplies and materials',
                'account_code': '5100'
            },
            
            # Professional Development
            {
                'name': 'Professional Development',
                'description': 'General professional development expenses',
                'account_code': '5110'
            },
            {
                'name': 'Continuing Legal Education',
                'description': 'CLE courses and legal education',
                'account_code': '5120'
            },
            {
                'name': 'Bar Association Dues',
                'description': 'Membership dues for bar associations',
                'account_code': '5130'
            },
            {
                'name': 'Professional Memberships',
                'description': 'Other professional organization memberships',
                'account_code': '5140'
            },
            
            # Marketing & Business Development
            {
                'name': 'Marketing & Advertising',
                'description': 'Marketing materials and advertising expenses',
                'account_code': '5150'
            },
            {
                'name': 'Website & Online Presence',
                'description': 'Website maintenance and online marketing',
                'account_code': '5160'
            },
            {
                'name': 'Business Development',
                'description': 'Client development and networking expenses',
                'account_code': '5170'
            },
            
            # Travel & Entertainment
            {
                'name': 'Travel & Entertainment',
                'description': 'General travel and entertainment expenses',
                'account_code': '5180'
            },
            {
                'name': 'Meals & Client Entertainment',
                'description': 'Client meals and entertainment expenses',
                'account_code': '5190'
            },
            
            # Insurance
            {
                'name': 'Professional Liability Insurance',
                'description': 'Legal malpractice and professional liability insurance',
                'account_code': '5200'
            },
            {
                'name': 'General Business Insurance',
                'description': 'General business and property insurance',
                'account_code': '5210'
            },
            {
                'name': 'Workers Compensation Insurance',
                'description': 'Workers compensation insurance coverage',
                'account_code': '5220'
            },
            
            # Depreciation & Amortization
            {
                'name': 'Depreciation Expense',
                'description': 'Depreciation of fixed assets',
                'account_code': '5230'
            },
            {
                'name': 'Amortization Expense',
                'description': 'Amortization of intangible assets',
                'account_code': '5240'
            },
            
            # Equipment & Maintenance
            {
                'name': 'Office Equipment Maintenance',
                'description': 'Maintenance and repair of office equipment',
                'account_code': '5250'
            },
            {
                'name': 'Computer & Software Maintenance',
                'description': 'IT maintenance and software licenses',
                'account_code': '5260'
            },
            
            # Legal Operations
            {
                'name': 'Legal Research Services',
                'description': 'Legal research databases and services',
                'account_code': '5270'
            },
            {
                'name': 'Court Filing Fees',
                'description': 'Fees for filing court documents',
                'account_code': '5280'
            },
            {
                'name': 'Process Serving Fees',
                'description': 'Fees for process serving services',
                'account_code': '5290'
            },
            {
                'name': 'Expert Witness Fees',
                'description': 'Fees paid to expert witnesses',
                'account_code': '5300'
            },
            {
                'name': 'Investigation Costs',
                'description': 'Investigation and research expenses',
                'account_code': '5310'
            },
            
            # Office Services
            {
                'name': 'Copying & Printing',
                'description': 'Document copying and printing expenses',
                'account_code': '5320'
            },
            {
                'name': 'Postage & Shipping',
                'description': 'Mail and shipping expenses',
                'account_code': '5330'
            },
            {
                'name': 'Telephone & Communications',
                'description': 'Phone and communication services',
                'account_code': '5340'
            },
            {
                'name': 'Internet & Data Services',
                'description': 'Internet and data service expenses',
                'account_code': '5350'
            },
            
            # Other Expenses
            {
                'name': 'Interest Expense',
                'description': 'Interest on loans and credit facilities',
                'account_code': '5360'
            },
            {
                'name': 'Income Tax Expense',
                'description': 'Income tax expenses',
                'account_code': '5370'
            },
            {
                'name': 'Bank Charges',
                'description': 'Bank fees and charges',
                'account_code': '5380'
            },
            {
                'name': 'Miscellaneous Expenses',
                'description': 'Other miscellaneous expenses',
                'account_code': '5390'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for category_data in categories_data:
            try:
                # Find the corresponding account
                account = Account.objects.get(code=category_data['account_code'])
                
                # Create or update the expense category
                category, created = ExpenseCategory.objects.get_or_create(
                    name=category_data['name'],
                    defaults={
                        'description': category_data['description'],
                        'account': account,
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created: {category.name}')
                    created_count += 1
                else:
                    # Update existing category
                    category.description = category_data['description']
                    category.account = account
                    category.is_active = True
                    category.save()
                    self.stdout.write(f'  Updated: {category.name}')
                    updated_count += 1
                    
            except Account.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Warning: Account {category_data["account_code"]} not found for {category_data["name"]}'
                    )
                )
        
        self.stdout.write('')
        self.stdout.write(f'Categories created: {created_count}')
        self.stdout.write(f'Categories updated: {updated_count}')
        self.stdout.write(f'Total categories: {created_count + updated_count}')
