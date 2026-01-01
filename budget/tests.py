from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Account, Transaction, BudgetPlan

class AccountTestCase(TestCase):
    def test_credit_account_validation(self):
        account = Account(
            name='Tarjeta',
            type='CREDITO',
            currency='PEN',
            opening_balance=Decimal('0.00'),
            credit_limit=Decimal('1000.00'),
            billing_cycle_day=15,
            due_day=30
        )
        account.full_clean()  # Should pass

        account.credit_limit = None
        with self.assertRaises(ValidationError):
            account.full_clean()

class TransactionTestCase(TestCase):
    def setUp(self):
        self.account = Account.objects.create(
            name='Efectivo',
            type='EFECTIVO',
            currency='PEN',
            opening_balance=Decimal('100.00')
        )

    def test_gasto_transaction(self):
        transaction = Transaction(
            date='2025-01-01',
            kind='GASTO',
            amount=Decimal('50.00'),
            currency='PEN',
            description='Compra',
            payment_method='EFECTIVO',
            account_from=self.account
        )
        transaction.full_clean()  # Should pass

        transaction.account_from = None
        with self.assertRaises(ValidationError):
            transaction.full_clean()

class BudgetPlanTestCase(TestCase):
    def test_budget_validation(self):
        budget = BudgetPlan(
            frequency='MENSUAL',
            period_start='2025-01-01',
            period_end='2025-01-31',
            currency='PEN',
            target_income=Decimal('2000.00'),
            target_expenses=Decimal('1500.00'),
            savings_rate=Decimal('10.00')
        )
        budget.full_clean()  # Should pass

        budget.savings_rate = Decimal('110.00')
        with self.assertRaises(ValidationError):
            budget.full_clean()
