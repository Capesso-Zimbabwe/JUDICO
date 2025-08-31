# Generated manually for Accounts Payable models

from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def set_default_timestamps(apps, schema_editor):
    """Set default timestamps for existing JournalEntryLine records"""
    JournalEntryLine = apps.get_model('finance_management', 'JournalEntryLine')
    # Update existing records with current timestamp
    JournalEntryLine.objects.filter(created_at__isnull=True).update(created_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ('finance_management', '0009_update_expense_models'),
    ]

    operations = [
        # First, add created_at field to JournalEntryLine if it doesn't exist
        migrations.AddField(
            model_name='journalentryline',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        
        # Run the data migration to set timestamps for existing records
        migrations.RunPython(set_default_timestamps, reverse_code=migrations.RunPython.noop),
        
        # Now make the field non-nullable
        migrations.AlterField(
            model_name='journalentryline',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        
        # Create AccountsPayable model
        migrations.CreateModel(
            name='AccountsPayable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_number', models.CharField(blank=True, max_length=50, unique=True)),
                ('vendor', models.CharField(max_length=255)),
                ('vendor_invoice_number', models.CharField(blank=True, max_length=100)),
                ('invoice_date', models.DateField()),
                ('due_date', models.DateField()),
                ('payment_terms', models.CharField(choices=[
                    ('IMMEDIATE', 'Immediate'),
                    ('NET_15', 'Net 15'),
                    ('NET_30', 'Net 30'),
                    ('NET_45', 'Net 45'),
                    ('NET_60', 'Net 60'),
                    ('NET_90', 'Net 90'),
                    ('CUSTOM', 'Custom'),
                ], default='NET_30', max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0.00, max_digits=15)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0.00, max_digits=15)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0.00, max_digits=15)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0.00, max_digits=15)),
                ('balance_due', models.DecimalField(decimal_places=2, default=0.00, max_digits=15)),
                ('status', models.CharField(choices=[
                    ('DRAFT', 'Draft'),
                    ('PENDING_APPROVAL', 'Pending Approval'),
                    ('APPROVED', 'Approved'),
                    ('PARTIALLY_PAID', 'Partially Paid'),
                    ('PAID', 'Paid'),
                    ('CANCELLED', 'Cancelled'),
                    ('OVERDUE', 'Overdue'),
                ], default='DRAFT', max_length=20)),
                ('is_recurring', models.BooleanField(default=False)),
                ('recurring_frequency', models.CharField(blank=True, max_length=20)),
                ('description', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('attachments', models.FileField(blank=True, upload_to='payables/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('paid_date', models.DateTimeField(blank=True, null=True)),
                ('payment_method', models.CharField(blank=True, max_length=50)),
                ('payment_reference', models.CharField(blank=True, max_length=100)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_payables', to='auth.user')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_payables', to='auth.user')),
                ('expense_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance_management.expensecategory')),
                ('journal_entry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance_management.journalentry')),
                ('paid_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paid_payables', to='auth.user')),
                ('period', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance_management.accountingperiod')),
            ],
            options={
                'verbose_name_plural': 'Accounts Payable',
                'ordering': ['-invoice_date', '-created_at'],
            },
        ),
        
        # Create AccountsPayableLineItem model
        migrations.CreateModel(
            name='AccountsPayableLineItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255)),
                ('quantity', models.DecimalField(decimal_places=2, default=1.00, max_digits=10)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=15)),
                ('tax_rate', models.DecimalField(decimal_places=4, default=0.00, max_digits=5)),
                ('line_total', models.DecimalField(decimal_places=2, default=0.00, max_digits=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expense_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance_management.account')),
                ('payable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='line_items', to='finance_management.accountspayable')),
            ],
            options={
                'verbose_name_plural': 'Accounts Payable Line Items',
                'ordering': ['id'],
            },
        ),
    ]
