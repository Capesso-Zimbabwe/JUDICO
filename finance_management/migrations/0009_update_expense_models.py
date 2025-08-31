# Generated manually to update existing expense models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance_management', '0008_remove_old_balance_field'),
    ]

    operations = [
        # Create ExpenseCategory model
        migrations.CreateModel(
            name='ExpenseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance_management.account')),
            ],
            options={
                'verbose_name_plural': 'Expense Categories',
                'ordering': ['name'],
            },
        ),
        
        # Create ExpenseLineItem model
        migrations.CreateModel(
            name='ExpenseLineItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=200)),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=15)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expense', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='line_items', to='finance_management.expense')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        
        # Add new fields to existing Expense model
        migrations.AddField(
            model_name='expense',
            name='reference_number',
            field=models.CharField(max_length=20, unique=True, null=True),
        ),
        migrations.AddField(
            model_name='expense',
            name='expense_type',
            field=models.CharField(choices=[('OPERATING', 'Operating Expense'), ('CAPITAL', 'Capital Expense'), ('PREPAID', 'Prepaid Expense'), ('ACCRUED', 'Accrued Expense')], default='OPERATING', max_length=20),
        ),
        migrations.AddField(
            model_name='expense',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='expense',
            name='paid_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='expense',
            name='payment_method',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='expense',
            name='payment_reference',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='expense',
            name='period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='finance_management.accountingperiod'),
        ),
        migrations.AddField(
            model_name='expense',
            name='expense_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='finance_management.expensecategory'),
        ),
        migrations.AddField(
            model_name='expense',
            name='paid_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expenses_paid', to='auth.user'),
        ),
        
        # Rename existing fields to match new structure
        migrations.RenameField(
            model_name='expense',
            old_name='amount',
            new_name='total_amount',
        ),
        migrations.RenameField(
            model_name='expense',
            old_name='vendor_name',
            new_name='vendor',
        ),
        migrations.RenameField(
            model_name='expense',
            old_name='submitted_by',
            new_name='created_by',
        ),
        
        # Remove old fields that are no longer needed
        migrations.RemoveField(
            model_name='expense',
            name='approval_level',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='approved_at',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='audit_trail',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='billable_amount',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='billable_status',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='case_number',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='client_case',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='compliance_notes',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='compliance_review_date',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='invoice_number',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='is_compliant',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='matter_type',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='reviewed_by',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='submitted_at',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='supporting_documents',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='tax_rate',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='vendor_tax_id',
        ),
        
        # Update status choices
        migrations.AlterField(
            model_name='expense',
            name='status',
            field=models.CharField(choices=[('DRAFT', 'Draft'), ('SUBMITTED', 'Submitted'), ('APPROVED', 'Approved'), ('PAID', 'Paid'), ('REJECTED', 'Rejected'), ('CANCELLED', 'Cancelled')], default='DRAFT', max_length=20),
        ),
        
        # Remove old indexes
        migrations.RemoveIndex(
            model_name='expense',
            name='finance_man_categor_a13831_idx',
        ),
        migrations.RemoveIndex(
            model_name='expense',
            name='finance_man_client__5ecac0_idx',
        ),
        migrations.RemoveIndex(
            model_name='expense',
            name='finance_man_billabl_fd6f0a_idx',
        ),
    ]
