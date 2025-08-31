from django.core.management.base import BaseCommand
from finance_management.models import AccountingPeriod

class Command(BaseCommand):
    help = 'List all existing accounting periods'

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Show only active (open) periods'
        )
        parser.add_argument(
            '--current',
            action='store_true',
            help='Show only current period'
        )

    def handle(self, *args, **options):
        queryset = AccountingPeriod.objects.all()
        
        if options['active_only']:
            queryset = queryset.filter(status='OPEN')
            self.stdout.write('Active (Open) Accounting Periods:')
        elif options['current']:
            queryset = queryset.filter(is_current=True)
            self.stdout.write('Current Accounting Period:')
        else:
            self.stdout.write('All Accounting Periods:')
        
        self.stdout.write('')
        
        if not queryset.exists():
            self.stdout.write('No periods found.')
            return
        
        # Display periods in a table format
        self.stdout.write(f"{'Name':<25} {'Start Date':<12} {'End Date':<12} {'Status':<10} {'Current':<8} {'Type':<12}")
        self.stdout.write('-' * 80)
        
        for period in queryset.order_by('start_date'):
            period_type = 'Adjustment' if period.is_adjustment_period else 'Regular'
            current_marker = '✓' if period.is_current else ''
            
            self.stdout.write(
                f"{period.name:<25} "
                f"{period.start_date.strftime('%Y-%m-%d'):<12} "
                f"{period.end_date.strftime('%Y-%m-%d'):<12} "
                f"{period.status:<10} "
                f"{current_marker:<8} "
                f"{period_type:<12}"
            )
        
        self.stdout.write('')
        self.stdout.write(f'Total periods: {queryset.count()}')
        
        # Show summary
        open_periods = AccountingPeriod.objects.filter(status='OPEN').count()
        closed_periods = AccountingPeriod.objects.filter(status='CLOSED').count()
        current_period = AccountingPeriod.objects.filter(is_current=True).first()
        
        self.stdout.write(f'Open periods: {open_periods}')
        self.stdout.write(f'Closed periods: {closed_periods}')
        
        if current_period:
            self.stdout.write(f'Current period: {current_period.name}')
        else:
            self.stdout.write('No current period set')
