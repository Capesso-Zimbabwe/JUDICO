from django.core.management.base import BaseCommand
from finance_management.models import Account
from django.db import transaction

class Command(BaseCommand):
    help = 'Populate the database with legal practice specific chart of accounts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate legal practice chart of accounts...'))
        
        # Clear existing accounts if any
        Account.objects.all().delete()
        
        with transaction.atomic():
            # ASSETS
            # Current Assets
            cash_checking = Account.objects.create(
                code='1000',
                name='Cash - Operating Account',
                account_type='ASSET',
                balance=50000.00,
                description='Primary operating checking account for daily transactions'
            )
            
            cash_trust = Account.objects.create(
                code='1010',
                name='Client Trust Account',
                account_type='ASSET',
                balance=125000.00,
                description='Client funds held in trust - IOLTA compliant account'
            )
            
            accounts_receivable = Account.objects.create(
                code='1200',
                name='Accounts Receivable - Legal Fees',
                account_type='ASSET',
                balance=75000.00,
                description='Outstanding legal fees owed by clients'
            )
            
            unbilled_time = Account.objects.create(
                code='1210',
                name='Unbilled Time and Expenses',
                account_type='ASSET',
                balance=25000.00,
                description='Work in progress - time and expenses not yet billed'
            )
            
            prepaid_expenses = Account.objects.create(
                code='1300',
                name='Prepaid Expenses',
                account_type='ASSET',
                balance=8000.00,
                description='Insurance, rent, and other prepaid expenses'
            )
            
            # Fixed Assets
            office_equipment = Account.objects.create(
                code='1500',
                name='Office Equipment',
                account_type='ASSET',
                balance=35000.00,
                description='Computers, printers, phones, and office equipment'
            )
            
            furniture_fixtures = Account.objects.create(
                code='1510',
                name='Furniture and Fixtures',
                account_type='ASSET',
                balance=20000.00,
                description='Office furniture, fixtures, and improvements'
            )
            
            law_library = Account.objects.create(
                code='1520',
                name='Law Library and Software',
                account_type='ASSET',
                balance=15000.00,
                description='Legal research materials, books, and software licenses'
            )
            
            # LIABILITIES
            # Current Liabilities
            accounts_payable = Account.objects.create(
                code='2000',
                name='Accounts Payable',
                account_type='LIABILITY',
                balance=12000.00,
                description='Outstanding bills and vendor payments'
            )
            
            client_advances = Account.objects.create(
                code='2010',
                name='Client Advances and Retainers',
                account_type='LIABILITY',
                balance=45000.00,
                description='Unearned client retainers and advance payments'
            )
            
            payroll_liabilities = Account.objects.create(
                code='2100',
                name='Payroll Liabilities',
                account_type='LIABILITY',
                balance=8500.00,
                description='Payroll taxes, benefits, and withholdings payable'
            )
            
            accrued_expenses = Account.objects.create(
                code='2200',
                name='Accrued Expenses',
                account_type='LIABILITY',
                balance=5000.00,
                description='Accrued salaries, utilities, and other expenses'
            )
            
            # Long-term Liabilities
            office_lease = Account.objects.create(
                code='2500',
                name='Office Lease Liability',
                account_type='LIABILITY',
                balance=0.00,
                description='Long-term office lease obligations'
            )
            
            # EQUITY
            partners_capital = Account.objects.create(
                code='3000',
                name='Partners Capital',
                account_type='EQUITY',
                balance=200000.00,
                description='Partners invested capital and retained earnings'
            )
            
            partners_drawings = Account.objects.create(
                code='3100',
                name='Partners Drawings',
                account_type='EQUITY',
                balance=0.00,
                description='Partner withdrawals and distributions'
            )
            
            # REVENUE
            # Legal Fee Revenue
            litigation_fees = Account.objects.create(
                code='4000',
                name='Litigation Fees',
                account_type='REVENUE',
                balance=0.00,
                description='Revenue from litigation and court representation'
            )
            
            corporate_fees = Account.objects.create(
                code='4010',
                name='Corporate and Business Law Fees',
                account_type='REVENUE',
                balance=0.00,
                description='Revenue from corporate law and business transactions'
            )
            
            real_estate_fees = Account.objects.create(
                code='4020',
                name='Real Estate Law Fees',
                account_type='REVENUE',
                balance=0.00,
                description='Revenue from real estate transactions and closings'
            )
            
            family_law_fees = Account.objects.create(
                code='4030',
                name='Family Law Fees',
                account_type='REVENUE',
                balance=0.00,
                description='Revenue from family law and domestic relations'
            )
            
            consultation_fees = Account.objects.create(
                code='4100',
                name='Consultation and Advisory Fees',
                account_type='REVENUE',
                balance=0.00,
                description='Revenue from legal consultations and advisory services'
            )
            
            # EXPENSES
            # Operating Expenses
            attorney_salaries = Account.objects.create(
                code='5000',
                name='Attorney Salaries',
                account_type='EXPENSE',
                balance=0.00,
                description='Salaries for attorneys and legal professionals'
            )
            
            staff_salaries = Account.objects.create(
                code='5010',
                name='Staff Salaries',
                account_type='EXPENSE',
                balance=0.00,
                description='Salaries for paralegals, secretaries, and support staff'
            )
            
            payroll_taxes = Account.objects.create(
                code='5020',
                name='Payroll Taxes and Benefits',
                account_type='EXPENSE',
                balance=0.00,
                description='Employer payroll taxes, health insurance, and benefits'
            )
            
            office_rent = Account.objects.create(
                code='5100',
                name='Office Rent',
                account_type='EXPENSE',
                balance=0.00,
                description='Monthly office rent and common area charges'
            )
            
            utilities = Account.objects.create(
                code='5110',
                name='Utilities',
                account_type='EXPENSE',
                balance=0.00,
                description='Electricity, water, gas, internet, and phone'
            )
            
            legal_research = Account.objects.create(
                code='5200',
                name='Legal Research and Databases',
                account_type='EXPENSE',
                balance=0.00,
                description='Westlaw, LexisNexis, and other legal research costs'
            )
            
            court_costs = Account.objects.create(
                code='5210',
                name='Court Costs and Filing Fees',
                account_type='EXPENSE',
                balance=0.00,
                description='Court filing fees, service costs, and legal expenses'
            )
            
            professional_liability = Account.objects.create(
                code='5300',
                name='Professional Liability Insurance',
                account_type='EXPENSE',
                balance=0.00,
                description='Malpractice and professional liability insurance'
            )
            
            continuing_education = Account.objects.create(
                code='5310',
                name='Continuing Legal Education',
                account_type='EXPENSE',
                balance=0.00,
                description='CLE courses, seminars, and professional development'
            )
            
            bar_dues = Account.objects.create(
                code='5320',
                name='Bar Dues and Professional Fees',
                account_type='EXPENSE',
                balance=0.00,
                description='State bar dues and professional association fees'
            )
            
            office_supplies = Account.objects.create(
                code='5400',
                name='Office Supplies',
                account_type='EXPENSE',
                balance=0.00,
                description='Paper, pens, folders, and general office supplies'
            )
            
            marketing = Account.objects.create(
                code='5500',
                name='Marketing and Business Development',
                account_type='EXPENSE',
                balance=0.00,
                description='Website, advertising, and client development costs'
            )
            
            travel_entertainment = Account.objects.create(
                code='5600',
                name='Travel and Entertainment',
                account_type='EXPENSE',
                balance=0.00,
                description='Business travel, meals, and client entertainment'
            )
            
            depreciation = Account.objects.create(
                code='5700',
                name='Depreciation Expense',
                account_type='EXPENSE',
                balance=0.00,
                description='Depreciation of office equipment and furniture'
            )
            
            bank_charges = Account.objects.create(
                code='5800',
                name='Bank Charges and Fees',
                account_type='EXPENSE',
                balance=0.00,
                description='Bank fees, credit card processing, and financial charges'
            )
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {Account.objects.count()} legal practice accounts'
            )
        )
        
        # Display summary by account type
        for account_type, _ in Account.ACCOUNT_TYPE_CHOICES:
            count = Account.objects.filter(account_type=account_type).count()
            self.stdout.write(f'  {account_type}: {count} accounts')