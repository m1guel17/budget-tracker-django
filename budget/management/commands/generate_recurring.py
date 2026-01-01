from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from budget.models import RecurringTransaction, Transaction, Payee

class Command(BaseCommand):
    help = 'Generate recurring transactions'

    def handle(self, *args, **options):
        today = timezone.now().date()
        recurrings = RecurringTransaction.objects.filter(is_active=True, next_run_date__lte=today)
        for rec in recurrings:
            if rec.end_date and rec.next_run_date > rec.end_date:
                rec.is_active = False
                rec.save()
                continue

            # Create transaction
            transaction = Transaction(
                date=rec.next_run_date,
                kind=rec.kind,
                amount=rec.amount,
                currency=rec.currency,
                category=rec.category,
                description=rec.description,
                payment_method=rec.payment_method,
                account_from=rec.account_from,
                account_to=rec.account_to,
                payee=rec.payee,
            )
            transaction.save()

            # Update next_run_date
            if rec.frequency == 'SEMANAL':
                rec.next_run_date += timedelta(weeks=1)
            elif rec.frequency == 'QUINCENAL':
                rec.next_run_date += timedelta(days=15)
            elif rec.frequency == 'MENSUAL':
                # Add one month
                if rec.next_run_date.month == 12:
                    rec.next_run_date = rec.next_run_date.replace(year=rec.next_run_date.year + 1, month=1)
                else:
                    rec.next_run_date = rec.next_run_date.replace(month=rec.next_run_date.month + 1)
            rec.save()

            self.stdout.write(self.style.SUCCESS(f'Created transaction for {rec} on {rec.next_run_date}'))