from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from finance_management.models import Account, Journal, AccountingPeriod

class Command(BaseCommand):
    help = 'Set up initial chart of accounts and journals for a law firm (NO periods created automatically)'

    def handle(self, *args, **options):
        self.stdout.write('Setting up law firm accounting system...')
        self.stdout.write('')
        
        # Create default journals
        self.create_default_journals()
        
        # Create default chart of accounts for law firm
        self.create_law_firm_chart_of_accounts()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Law firm accounting system setup completed successfully!'))
        self.stdout.write('')
        self.stdout.write('IMPORTANT: No accounting periods were created automatically.')
        self.stdout.write('')
        self.stdout.write('To create periods when you need them:')
        self.stdout.write('1. Use Django admin: /admin/finance_management/accountingperiod/')
        self.stdout.write('2. Or use command: python manage.py create_periods YEAR')
        self.stdout.write('3. Or create them through the application interface')
        self.stdout.write('')
        self.stdout.write('This gives you complete control over when and which periods to create.')

    def create_default_journals(self):
        """Create default journals"""
        journals_data = [
            {
                'code': 'GJ',
                'name': 'General Journal',
                'journal_type': 'GENERAL',
                'description': 'Default general journal for all transactions',
                'status': 'ACTIVE'
            },
            {
                'code': 'SJ',
                'name': 'Sales Journal',
                'journal_type': 'SALES',
                'description': 'Journal for recording legal services revenue',
                'status': 'ACTIVE'
            },
            {
                'code': 'PJ',
                'name': 'Purchase Journal',
                'journal_type': 'PURCHASE',
                'description': 'Journal for recording purchase transactions',
                'status': 'ACTIVE'
            },
            {
                'code': 'CRJ',
                'name': 'Cash Receipts Journal',
                'journal_type': 'CASH_RECEIPTS',
                'description': 'Journal for recording cash receipts and client payments',
                'status': 'ACTIVE'
            },
            {
                'code': 'CDJ',
                'name': 'Cash Disbursements Journal',
                'journal_type': 'CASH_DISBURSEMENTS',
                'description': 'Journal for recording cash disbursements',
                'status': 'ACTIVE'
            },
            {
                'code': 'AJ',
                'name': 'Adjusting Journal',
                'journal_type': 'ADJUSTING',
                'description': 'Journal for period-end adjustments',
                'status': 'ACTIVE'
            },
            {
                'code': 'CLOSING',
                'name': 'Closing Journal',
                'journal_type': 'CLOSING',
                'description': 'Journal for period closing entries',
                'status': 'ACTIVE'
            }
        ]
        
        for journal_data in journals_data:
            journal, created = Journal.objects.get_or_create(
                code=journal_data['code'],
                defaults=journal_data
            )
            if created:
                self.stdout.write(f'Created journal: {journal.name}')
            else:
                self.stdout.write(f'Journal already exists: {journal.name}')

    def create_law_firm_chart_of_accounts(self):
        """Create chart of accounts specifically for a law firm"""
        accounts_data = [
            # Assets (1000-1999)
            {'code': '1000', 'name': 'Cash on Hand', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT', 'is_cash_account': True},
            {'code': '1010', 'name': 'Operating Bank Account', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT', 'is_bank_account': True},
            {'code': '1020', 'name': 'Trust Account', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT', 'is_bank_account': True},
            {'code': '1030', 'name': 'Client Trust Funds', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1040', 'name': 'Accounts Receivable - Legal Fees', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1050', 'name': 'Accounts Receivable - Disbursements', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1060', 'name': 'Prepaid Expenses', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1070', 'name': 'Prepaid Insurance', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1080', 'name': 'Prepaid Rent', 'account_type': 'ASSET', 'account_category': 'CURRENT_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1500', 'name': 'Office Equipment', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1510', 'name': 'Accumulated Depreciation - Office Equipment', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'CREDIT', 'is_contra_account': True},
            {'code': '1520', 'name': 'Computer Equipment', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1530', 'name': 'Accumulated Depreciation - Computer Equipment', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'CREDIT', 'is_contra_account': True},
            {'code': '1540', 'name': 'Furniture & Fixtures', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1550', 'name': 'Accumulated Depreciation - Furniture & Fixtures', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'CREDIT', 'is_contra_account': True},
            {'code': '1560', 'name': 'Law Library', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1570', 'name': 'Accumulated Depreciation - Law Library', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'CREDIT', 'is_contra_account': True},
            {'code': '1600', 'name': 'Office Building', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1610', 'name': 'Accumulated Depreciation - Office Building', 'account_type': 'ASSET', 'account_category': 'FIXED_ASSET', 'normal_balance': 'CREDIT', 'is_contra_account': True},
            {'code': '1700', 'name': 'Intangible Assets', 'account_type': 'ASSET', 'account_category': 'INTANGIBLE_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1710', 'name': 'Goodwill', 'account_type': 'ASSET', 'account_category': 'INTANGIBLE_ASSET', 'normal_balance': 'DEBIT'},
            {'code': '1720', 'name': 'Client Lists', 'account_type': 'ASSET', 'account_category': 'INTANGIBLE_ASSET', 'normal_balance': 'DEBIT'},
            
            # Liabilities (2000-2999)
            {'code': '2000', 'name': 'Accounts Payable - Vendors', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2010', 'name': 'Accounts Payable - Court Costs', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2020', 'name': 'Accrued Expenses', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2030', 'name': 'Accrued Payroll', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2040', 'name': 'Accrued Payroll Taxes', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2050', 'name': 'Income Tax Payable', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2060', 'name': 'Sales Tax Payable', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2070', 'name': 'Client Trust Liabilities', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2080', 'name': 'Unearned Legal Fees', 'account_type': 'LIABILITY', 'account_category': 'CURRENT_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2500', 'name': 'Long-term Loans', 'account_type': 'LIABILITY', 'account_category': 'LONG_TERM_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2510', 'name': 'Mortgage Payable', 'account_type': 'LIABILITY', 'account_category': 'LONG_TERM_LIABILITY', 'normal_balance': 'CREDIT'},
            {'code': '2520', 'name': 'Equipment Loans', 'account_type': 'LIABILITY', 'account_category': 'LONG_TERM_LIABILITY', 'normal_balance': 'CREDIT'},
            
            # Equity (3000-3999)
            {'code': '3000', 'name': 'Retained Earnings', 'account_type': 'EQUITY', 'account_category': 'RETAINED_EARNINGS', 'normal_balance': 'CREDIT'},
            {'code': '3010', 'name': 'Partner Capital', 'account_type': 'EQUITY', 'account_category': 'OWNERS_EQUITY', 'normal_balance': 'CREDIT'},
            {'code': '3020', 'name': 'Partner Withdrawals', 'account_type': 'EQUITY', 'account_category': 'OWNERS_EQUITY', 'normal_balance': 'DEBIT'},
            {'code': '3030', 'name': 'Additional Paid-in Capital', 'account_type': 'EQUITY', 'account_category': 'OWNERS_EQUITY', 'normal_balance': 'CREDIT'},
            {'code': '3040', 'name': 'Treasury Stock', 'account_type': 'EQUITY', 'account_category': 'OWNERS_EQUITY', 'normal_balance': 'DEBIT', 'is_contra_account': True},
            
            # Revenue (4000-4999)
            {'code': '4000', 'name': 'Legal Services Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4010', 'name': 'Litigation Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4020', 'name': 'Corporate Law Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4030', 'name': 'Real Estate Law Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4040', 'name': 'Family Law Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4050', 'name': 'Criminal Law Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4060', 'name': 'Estate Planning Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4070', 'name': 'Tax Law Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4080', 'name': 'Consulting Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4090', 'name': 'Document Preparation Revenue', 'account_type': 'REVENUE', 'account_category': 'OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4100', 'name': 'Interest Income', 'account_type': 'REVENUE', 'account_category': 'NON_OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            {'code': '4110', 'name': 'Other Income', 'account_type': 'REVENUE', 'account_category': 'NON_OPERATING_REVENUE', 'normal_balance': 'CREDIT'},
            
            # Expenses (5000-5999)
            {'code': '5000', 'name': 'Partner Salaries', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5010', 'name': 'Associate Attorney Salaries', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5020', 'name': 'Paralegal Salaries', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5030', 'name': 'Legal Secretary Salaries', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5040', 'name': 'Administrative Staff Salaries', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5050', 'name': 'Employee Benefits', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5060', 'name': 'Payroll Taxes', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5070', 'name': 'Office Rent', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5080', 'name': 'Utilities', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5090', 'name': 'Office Supplies', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5100', 'name': 'Legal Supplies', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5110', 'name': 'Professional Development', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5120', 'name': 'Continuing Legal Education', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5130', 'name': 'Bar Association Dues', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5140', 'name': 'Professional Memberships', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5150', 'name': 'Marketing & Advertising', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5160', 'name': 'Website & Online Presence', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5170', 'name': 'Business Development', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5180', 'name': 'Travel & Entertainment', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5190', 'name': 'Meals & Client Entertainment', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5200', 'name': 'Insurance - Professional Liability', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5210', 'name': 'Insurance - General Business', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5220', 'name': 'Insurance - Workers Compensation', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5230', 'name': 'Depreciation Expense', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5240', 'name': 'Amortization Expense', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5250', 'name': 'Office Equipment Maintenance', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5260', 'name': 'Computer & Software Maintenance', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5270', 'name': 'Legal Research Services', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5280', 'name': 'Court Filing Fees', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5290', 'name': 'Process Serving Fees', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5300', 'name': 'Expert Witness Fees', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5310', 'name': 'Investigation Costs', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5320', 'name': 'Copying & Printing', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5330', 'name': 'Postage & Shipping', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5340', 'name': 'Telephone & Communications', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5350', 'name': 'Internet & Data Services', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5360', 'name': 'Interest Expense', 'account_type': 'EXPENSE', 'account_category': 'NON_OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5370', 'name': 'Income Tax Expense', 'account_type': 'EXPENSE', 'account_category': 'NON_OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5380', 'name': 'Bank Charges', 'account_type': 'EXPENSE', 'account_category': 'NON_OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
            {'code': '5390', 'name': 'Miscellaneous Expenses', 'account_type': 'EXPENSE', 'account_category': 'OPERATING_EXPENSE', 'normal_balance': 'DEBIT'},
        ]
        
        for account_data in accounts_data:
            account, created = Account.objects.get_or_create(
                code=account_data['code'],
                defaults=account_data
            )
            if created:
                self.stdout.write(f'Created account: {account.code} - {account.name}')
            else:
                self.stdout.write(f'Account already exists: {account.code} - {account.name}')
