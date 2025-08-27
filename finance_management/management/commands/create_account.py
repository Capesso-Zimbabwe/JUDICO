from django.core.management.base import BaseCommand
from finance_management.models import Account
from django.db import transaction

class Command(BaseCommand):
    help = 'Create a new account in the chart of accounts'

    def handle(self, *args, **options):
        try:
            # Show available account types
            self.stdout.write('\nAvailable Account Types:')
            for code, name in Account.ACCOUNT_TYPE_CHOICES:
                self.stdout.write(f'{code}: {name}')

            # Get account details
            code = self.get_input('Enter account code: ')
            name = self.get_input('Enter account name: ')
            
            while True:
                account_type = self.get_input('Enter account type (from the list above): ').upper()
                if account_type in [t[0] for t in Account.ACCOUNT_TYPE_CHOICES]:
                    break
                self.stdout.write(self.style.ERROR('Invalid account type'))

            description = self.get_input('Enter description (optional): ')
            
            # Show available status options
            self.stdout.write('\nAvailable Status Options:')
            for code, name in Account.STATUS_CHOICES:
                self.stdout.write(f'{code}: {name}')
            
            while True:
                status = self.get_input('Enter status (ACTIVE/INACTIVE): ').upper()
                if status in [s[0] for s in Account.STATUS_CHOICES]:
                    break
                self.stdout.write(self.style.ERROR('Invalid status'))

            # Show existing accounts for parent selection
            self.stdout.write('\nExisting Accounts:')
            accounts = Account.objects.all().order_by('code')
            for account in accounts:
                self.stdout.write(f'{account.code}: {account.name}')

            parent_code = self.get_input('\nEnter parent account code (optional, press Enter to skip): ')
            parent_account = None
            if parent_code:
                try:
                    parent_account = Account.objects.get(code=parent_code)
                except Account.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Parent account {parent_code} not found'))
                    return

            # Create the account
            with transaction.atomic():
                account = Account.objects.create(
                    code=code,
                    name=name,
                    account_type=account_type,
                    description=description,
                    status=status,
                    parent_account=parent_account,
                    balance=0
                )

                self.stdout.write(self.style.SUCCESS(f'\nAccount created successfully:'))
                self.stdout.write(f'Code: {account.code}')
                self.stdout.write(f'Name: {account.name}')
                self.stdout.write(f'Type: {account.get_account_type_display()}')
                self.stdout.write(f'Status: {account.get_status_display()}')
                if parent_account:
                    self.stdout.write(f'Parent Account: {parent_account.code} - {parent_account.name}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def get_input(self, prompt):
        return input(prompt).strip()
