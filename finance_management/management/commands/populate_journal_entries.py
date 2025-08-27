from django.core.management.base import BaseCommand
from finance_management.models import Account, JournalEntry, JournalEntryLine
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate the database with sample journal entries'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate sample journal entries...'))
        
        try:
            # Get the first admin user or create one if none exists
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin'
                )

            with transaction.atomic():
                # Create a journal entry for initial cash deposit
                cash_account = Account.objects.get(code='1000')  # Operating Account
                capital_account = Account.objects.get(code='3000')  # Owner's Capital

                # Delete any existing journal entries
                JournalEntry.objects.all().delete()

                # 1. Initial capital investment
                initial_deposit = JournalEntry.objects.create(
                    entry_number='JE-2024-001',
                    description='Initial capital investment',
                    status='POSTED',
                    created_by=admin_user,
                    total_debit=Decimal('500000.00'),
                    total_credit=Decimal('500000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=initial_deposit,
                    account=cash_account,
                    description='Initial capital investment',
                    debit=Decimal('500000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=initial_deposit,
                    account=capital_account,
                    description='Initial capital investment',
                    credit=Decimal('500000.00')
                )

                # 2. Purchase of office equipment and furniture
                equipment_purchase = JournalEntry.objects.create(
                    entry_number='JE-2024-002',
                    description='Purchase of office equipment and furniture',
                    status='POSTED',
                    created_by=admin_user,
                    total_debit=Decimal('150000.00'),
                    total_credit=Decimal('150000.00')
                )

                office_equipment = Account.objects.get(code='1500')
                furniture = Account.objects.get(code='1510')

                JournalEntryLine.objects.create(
                    journal_entry=equipment_purchase,
                    account=office_equipment,
                    description='Purchase of computers and office equipment',
                    debit=Decimal('100000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=equipment_purchase,
                    account=furniture,
                    description='Purchase of office furniture',
                    debit=Decimal('50000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=equipment_purchase,
                    account=cash_account,
                    description='Payment for office equipment and furniture',
                    credit=Decimal('150000.00')
                )

                # 3. Legal fees billed to clients
                ar_account = Account.objects.get(code='1200')
                revenue_account = Account.objects.get(code='4000')

                legal_fees = JournalEntry.objects.create(
                    entry_number='JE-2024-003',
                    description='Legal fees billed to clients',
                    status='POSTED',
                    created_by=admin_user,
                    total_debit=Decimal('250000.00'),
                    total_credit=Decimal('250000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=legal_fees,
                    account=ar_account,
                    description='Legal fees billed',
                    debit=Decimal('250000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=legal_fees,
                    account=revenue_account,
                    description='Legal fees earned',
                    credit=Decimal('250000.00')
                )

                # 4. Client trust deposits
                trust_account = Account.objects.get(code='1010')
                client_advances = Account.objects.get(code='2010')

                trust_deposits = JournalEntry.objects.create(
                    entry_number='JE-2024-004',
                    description='Client trust deposits received',
                    status='POSTED',
                    created_by=admin_user,
                    total_debit=Decimal('175000.00'),
                    total_credit=Decimal('175000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=trust_deposits,
                    account=trust_account,
                    description='Client trust deposits',
                    debit=Decimal('175000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=trust_deposits,
                    account=client_advances,
                    description='Client trust liability',
                    credit=Decimal('175000.00')
                )

                # 5. Partial payment received from clients
                payment_received = JournalEntry.objects.create(
                    entry_number='JE-2024-005',
                    description='Payment received from clients',
                    status='POSTED',
                    created_by=admin_user,
                    total_debit=Decimal('180000.00'),
                    total_credit=Decimal('180000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=payment_received,
                    account=cash_account,
                    description='Client payment received',
                    debit=Decimal('180000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=payment_received,
                    account=ar_account,
                    description='Reduction in accounts receivable',
                    credit=Decimal('180000.00')
                )

                # 6. Operating expenses
                expenses = {
                    '5000': Decimal('85000.00'),  # Attorney Salaries
                    '5010': Decimal('45000.00'),  # Staff Salaries
                    '5100': Decimal('25000.00'),  # Office Rent
                    '5110': Decimal('8000.00'),   # Utilities
                    '5200': Decimal('12000.00'),  # Legal Research
                    '5400': Decimal('5000.00'),   # Office Supplies
                }

                operating_expenses = JournalEntry.objects.create(
                    entry_number='JE-2024-006',
                    description='Monthly operating expenses',
                    status='POSTED',
                    created_by=admin_user,
                    total_debit=sum(expenses.values()),
                    total_credit=sum(expenses.values())
                )

                for code, amount in expenses.items():
                    expense_account = Account.objects.get(code=code)
                    JournalEntryLine.objects.create(
                        journal_entry=operating_expenses,
                        account=expense_account,
                        description=f'Monthly {expense_account.name.lower()}',
                        debit=amount
                    )

                JournalEntryLine.objects.create(
                    journal_entry=operating_expenses,
                    account=cash_account,
                    description='Payment of operating expenses',
                    credit=sum(expenses.values())
                )

                # 7. Prepaid expenses
                prepaid_account = Account.objects.get(code='1300')
                prepaid_entry = JournalEntry.objects.create(
                    entry_number='JE-2024-007',
                    description='Prepaid insurance and subscriptions',
                    status='POSTED',
                    created_by=admin_user,
                    total_debit=Decimal('35000.00'),
                    total_credit=Decimal('35000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=prepaid_entry,
                    account=prepaid_account,
                    description='Annual insurance and software subscriptions',
                    debit=Decimal('35000.00')
                )

                JournalEntryLine.objects.create(
                    journal_entry=prepaid_entry,
                    account=cash_account,
                    description='Payment for prepaid expenses',
                    credit=Decimal('35000.00')
                )

            self.stdout.write(self.style.SUCCESS('Successfully populated sample journal entries'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
