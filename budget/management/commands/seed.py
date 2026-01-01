from django.core.management.base import BaseCommand
from budget.models import Category, Account
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed initial data'

    def handle(self, *args, **options):
        # Categories
        categories = [
            'Alimentación',
            'Transporte',
            'Servicios',
            'Ocio',
            'Salud',
            'Educación',
            'Vivienda',
            'Otros'
        ]
        for cat in categories:
            Category.objects.get_or_create(name=cat, defaults={'is_active': True})
            self.stdout.write(self.style.SUCCESS(f'Created category: {cat}'))

        # Efectivo account
        account, created = Account.objects.get_or_create(
            name='Efectivo',
            defaults={
                'type': 'EFECTIVO',
                'currency': 'PEN',
                'opening_balance': Decimal('0.00')
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created account: Efectivo'))
        else:
            self.stdout.write('Account Efectivo already exists')