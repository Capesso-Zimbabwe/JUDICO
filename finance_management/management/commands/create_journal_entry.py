from django.core.management.base import BaseCommand
from finance_management.models import Account, JournalEntry, JournalEntryLine
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal, InvalidOperation
import datetime

class Command(BaseCommand):
    help = 'Create a new journal entry with lines'

    def add_arguments(self, parser):
        parser.add_argument('--batch', action='store_true', help='Run in batch mode without prompts')

    def handle(self, *args, **options):
        try:
            # Get the first admin user or create one if none exists
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin'
                )

            # Get entry details
            entry_number = self.get_input('Enter journal entry number (e.g., JE-2024-001): ')
            date_str = self.get_input('Enter date (YYYY-MM-DD): ', validate=self.validate_date)
            description = self.get_input('Enter description: ')

            # Create the journal entry
            with transaction.atomic():
                journal_entry = JournalEntry.objects.create(
                    entry_number=entry_number,
                    date=datetime.datetime.strptime(date_str, '%Y-%m-%d').date(),
                    description=description,
                    status='POSTED',
                    created_by=admin_user
                )

                # Display available accounts
                self.stdout.write('\nAvailable Accounts:')
                accounts = Account.objects.all().order_by('code')
                for account in accounts:
                    self.stdout.write(f'{account.code}: {account.name} ({account.get_account_type_display()})')

                lines = []
                total_debit = Decimal('0.00')
                total_credit = Decimal('0.00')

                while True:
                    self.stdout.write('\nAdd journal entry line:')
                    account_code = self.get_input('Enter account code (or press Enter to finish): ')
                    if not account_code:
                        break

                    try:
                        account = Account.objects.get(code=account_code)
                    except Account.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'Account {account_code} not found'))
                        continue

                    description = self.get_input('Enter line description: ')
                    
                    # Get debit amount
                    debit_str = self.get_input('Enter debit amount (0 if none): ', validate=self.validate_decimal)
                    debit = Decimal(debit_str) if debit_str else Decimal('0.00')
                    
                    # Get credit amount
                    credit_str = self.get_input('Enter credit amount (0 if none): ', validate=self.validate_decimal)
                    credit = Decimal(credit_str) if credit_str else Decimal('0.00')

                    if debit > 0 and credit > 0:
                        self.stdout.write(self.style.ERROR('An entry cannot have both debit and credit'))
                        continue

                    if debit == 0 and credit == 0:
                        self.stdout.write(self.style.ERROR('Either debit or credit must be greater than 0'))
                        continue

                    lines.append({
                        'account': account,
                        'description': description,
                        'debit': debit,
                        'credit': credit
                    })

                    total_debit += debit
                    total_credit += credit

                    self.stdout.write(f'\nCurrent Totals:')
                    self.stdout.write(f'Total Debits:  ${total_debit:,.2f}')
                    self.stdout.write(f'Total Credits: ${total_credit:,.2f}')
                    self.stdout.write(f'Difference:    ${total_debit - total_credit:,.2f}')

                if not lines:
                    self.stdout.write(self.style.ERROR('No lines entered. Cancelling entry.'))
                    return

                if total_debit != total_credit:
                    self.stdout.write(self.style.ERROR('Journal entry is not balanced. Debits must equal credits.'))
                    return

                # Update journal entry totals
                journal_entry.total_debit = total_debit
                journal_entry.total_credit = total_credit
                journal_entry.save()

                # Create journal entry lines
                for line in lines:
                    JournalEntryLine.objects.create(
                        journal_entry=journal_entry,
                        account=line['account'],
                        description=line['description'],
                        debit=line['debit'],
                        credit=line['credit']
                    )

                self.stdout.write(self.style.SUCCESS(f'\nJournal entry {entry_number} created successfully'))
                self.stdout.write(f'Total Amount: ${total_debit:,.2f}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def get_input(self, prompt, validate=None):
        while True:
            value = input(prompt)
            if validate:
                try:
                    validate(value)
                    return value
                except ValueError as e:
                    self.stdout.write(self.style.ERROR(str(e)))
            else:
                return value

    def validate_date(self, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            raise ValueError('Invalid date format. Use YYYY-MM-DD')

    def validate_decimal(self, value):
        if not value:
            return True
        try:
            amount = Decimal(value)
            if amount < 0:
                raise ValueError('Amount cannot be negative')
            return True
        except InvalidOperation:
            raise ValueError('Invalid decimal number')
