from decimal import Decimal
from django import template

register = template.Library()


@register.filter(name='sum_payments')
def sum_payments(payments):
    """Sum the 'amount' field of a list/queryset of payment objects.

    Usage: {{ payments|sum_payments }}
    """
    if payments is None:
        return Decimal('0')

    total = Decimal('0')
    try:
        iterable = payments.all() if hasattr(payments, 'all') else payments
        for payment in iterable:
            amount = getattr(payment, 'amount', 0) or 0
            total += Decimal(str(amount))
        return total
    except Exception:
        return Decimal('0')


