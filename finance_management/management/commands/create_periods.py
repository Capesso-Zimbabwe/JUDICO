from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import date, timedelta
from finance_management.models import AccountingPeriod

class Command(BaseCommand):
    help = 'Create accounting periods for a specific year (e.g., python manage.py create_periods 2026)'

    def add_arguments(self, parser):
        parser.add_argument(
            'year',
            type=int,
            help='Year for which to create accounting periods'
        )
        parser.add_argument(
            '--monthly',
            action='store_true',
            help='Create monthly periods (default)'
        )
        parser.add_argument(
            '--quarterly',
            action='store_true',
            help='Create quarterly periods instead of monthly'
        )
        parser.add_argument(
            '--adjustment',
            action='store_true',
            help='Create adjustment period for year-end'
        )

    def handle(self, *args, **options):
        year = options['year']
        is_monthly = not options['quarterly']  # Default to monthly
        create_adjustment = options['adjustment']
        
        self.stdout.write(f'Creating accounting periods for {year}...')
        
        if is_monthly:
            self.create_monthly_periods(year)
        else:
            self.create_quarterly_periods(year)
        
        if create_adjustment:
            self.create_adjustment_period(year)
        
        self.stdout.write(self.style.SUCCESS(f'Accounting periods for {year} created successfully!'))

    def create_monthly_periods(self, year):
        """Create monthly periods for the specified year"""
        for month in range(1, 13):
            month_name = date(year, month, 1).strftime('%B %Y')
            start_date = date(year, month, 1)
            
            # Calculate end date (last day of month)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Set current period to the current month and year
            is_current = (month == timezone.now().month and year == timezone.now().year)
            
            period, created = AccountingPeriod.objects.get_or_create(
                name=month_name,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    'status': 'OPEN',
                    'is_current': is_current,
                    'is_adjustment_period': False
                }
            )
            
            if created:
                self.stdout.write(f'  Created period: {period.name}')
            else:
                self.stdout.write(f'  Period already exists: {period.name}')

    def create_quarterly_periods(self, year):
        """Create quarterly periods for the specified year"""
        quarters = [
            ('Q1', date(year, 1, 1), date(year, 3, 31)),
            ('Q2', date(year, 4, 1), date(year, 6, 30)),
            ('Q3', date(year, 7, 1), date(year, 9, 30)),
            ('Q4', date(year, 10, 1), date(year, 12, 31)),
        ]
        
        for quarter_name, start_date, end_date in quarters:
            period_name = f'{quarter_name} {year}'
            
            # Set current period to the current quarter and year
            current_date = timezone.now().date()
            is_current = (start_date <= current_date <= end_date and year == current_date.year)
            
            period, created = AccountingPeriod.objects.get_or_create(
                name=period_name,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    'status': 'OPEN',
                    'is_current': is_current,
                    'is_adjustment_period': False
                }
            )
            
            if created:
                self.stdout.write(f'  Created period: {period.name}')
            else:
                self.stdout.write(f'  Period already exists: {period.name}')

    def create_adjustment_period(self, year):
        """Create adjustment period for year-end"""
        adjustment_period, created = AccountingPeriod.objects.get_or_create(
            name=f'Adjustments {year}',
            start_date=date(year, 12, 31),
            end_date=date(year, 12, 31),
            defaults={
                'status': 'OPEN',
                'is_current': False,
                'is_adjustment_period': True
            }
        )
        
        if created:
            self.stdout.write(f'  Created adjustment period: {adjustment_period.name}')
        else:
            self.stdout.write(f'  Adjustment period already exists: {adjustment_period.name}')
