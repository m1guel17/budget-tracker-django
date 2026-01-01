from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, F, Case, When, Value, DecimalField
from django.core.exceptions import ValidationError

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


class Payee(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Destinatario"
        verbose_name_plural = "Destinatarios"


class ExchangeRate(models.Model):
    date = models.DateField(unique=True)
    usd_to_pen = models.DecimalField(max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal('0.01'))])

    def __str__(self):
        return f"{self.date}: 1 USD = {self.usd_to_pen} PEN"

    class Meta:
        verbose_name = "Tipo de Cambio"
        verbose_name_plural = "Tipos de Cambio"
        ordering = ['-date']


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('EFECTIVO', 'Efectivo'),
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
    ]
    CURRENCIES = [
        ('PEN', 'PEN'),
        ('USD', 'USD'),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='PEN')
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    # Conditional fields
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    billing_cycle_day = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    due_day = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    savings_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def clean(self):
        if self.type == 'CREDITO':
            if not self.credit_limit or not self.billing_cycle_day or not self.due_day:
                raise ValidationError("Las cuentas de crédito requieren límite, día de ciclo y día de vencimiento.")
            if self.billing_cycle_day > 31 or self.due_day > 31:
                raise ValidationError("Los días deben estar entre 1 y 31.")
        elif self.type == 'DEBITO':
            if not self.savings_amount:
                raise ValidationError("Las cuentas de débito requieren monto de ahorro.")
        else:  # EFECTIVO
            if self.credit_limit or self.billing_cycle_day or self.due_day or self.savings_amount:
                raise ValidationError("Las cuentas de efectivo no tienen campos adicionales.")

    @property
    def balance(self):
        # Calculate balance based on valid transactions
        from django.db.models import Q
        inflows = Transaction.objects.filter(
            Q(kind='INGRESO', account_to=self) |
            Q(kind='TRANSFERENCIA', account_to=self) |
            Q(kind='PAGO_TARJETA', account_to=self) |
            Q(kind='TRANSFERENCIA_EXTERNA', account_to=self),
            is_valid=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        outflows = Transaction.objects.filter(
            Q(kind='GASTO', account_from=self) |
            Q(kind='TRANSFERENCIA', account_from=self) |
            Q(kind='PAGO_TARJETA', account_from=self) |
            Q(kind='TRANSFERENCIA_EXTERNA', account_from=self),
            is_valid=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return self.opening_balance + inflows - outflows

    @property
    def credit_used(self):
        if self.type != 'CREDITO':
            return Decimal('0.00')
        # Sum of GASTO with payment_method=TARJETA_CREDITO from this account
        # Minus sum of PAGO_TARJETA to this account
        used = Transaction.objects.filter(account_from=self, kind='GASTO', payment_method='TARJETA_CREDITO', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        paid = Transaction.objects.filter(account_to=self, kind='PAGO_TARJETA', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return used - paid

    @property
    def available_credit(self):
        if self.type != 'CREDITO':
            return None
        return self.credit_limit - self.credit_used

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    class Meta:
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"


class Transaction(models.Model):
    KINDS = [
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('PAGO_TARJETA', 'Pago de Tarjeta'),
        ('TRANSFERENCIA_EXTERNA', 'Transf. Externa'),
    ]
    PAYMENT_METHODS = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA_DEBITO', 'Tarjeta de Débito'),
        ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('OTRO', 'Otro'),
    ]

    date = models.DateField()
    effective_period = models.DateField()
    kind = models.CharField(max_length=25, choices=KINDS)
    is_valid = models.BooleanField(default=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, choices=Account.CURRENCIES, default='PEN')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS)

    account_from = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='transactions_from')
    account_to = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='transactions_to')
    payee = models.ForeignKey(Payee, on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        if self.kind == 'GASTO':
            if not self.account_from:
                raise ValidationError("Los gastos requieren cuenta de origen.")
            if self.account_to:
                raise ValidationError("Los gastos no tienen cuenta de destino.")
        elif self.kind == 'INGRESO':
            if not self.account_to:
                raise ValidationError("Los ingresos requieren cuenta de destino.")
            if self.account_from:
                raise ValidationError("Los ingresos no tienen cuenta de origen.")
        elif self.kind == 'TRANSFERENCIA':
            if not self.account_from or not self.account_to:
                raise ValidationError("Las transferencias requieren cuenta de origen y destino.")
            if self.account_from == self.account_to:
                raise ValidationError("No se puede transferir a la misma cuenta.")
        elif self.kind == 'PAGO_TARJETA':
            if not self.account_from or not self.account_to:
                raise ValidationError("Los pagos de tarjeta requieren cuenta de origen y destino.")
            if self.account_to.type != 'CREDITO':
                raise ValidationError("El destino debe ser una cuenta de crédito.")
            if self.account_from.type == 'CREDITO':
                raise ValidationError("El origen no puede ser una cuenta de crédito.")
        elif self.kind == 'TRANSFERENCIA_EXTERNA':
            if not ((self.account_from and not self.account_to) or (not self.account_from and self.account_to)):
                raise ValidationError("Las transferencias externas requieren una cuenta interna (origen o destino) y un destinatario externo.")
            if self.account_from and self.account_to:
                raise ValidationError("Las transferencias externas no pueden tener ambas cuentas internas.")
        # Effective period is first day of the month of date
        self.effective_period = self.date.replace(day=1)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_kind_display()} - {self.amount} {self.currency} - {self.date}"

    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        ordering = ['-date']


class RecurringTransaction(models.Model):
    FREQUENCIES = [
        ('SEMANAL', 'Semanal'),
        ('QUINCENAL', 'Quincenal'),
        ('MENSUAL', 'Mensual'),
    ]

    is_active = models.BooleanField(default=True)
    kind = models.CharField(max_length=25, choices=Transaction.KINDS)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, choices=Account.CURRENCIES, default='PEN')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=15, choices=Transaction.PAYMENT_METHODS)
    account_from = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='recurring_from')
    account_to = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='recurring_to')
    payee = models.ForeignKey(Payee, on_delete=models.SET_NULL, null=True, blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCIES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_run_date = models.DateField()

    def clean(self):
        # Similar validations as Transaction
        if self.kind == 'GASTO':
            if not self.account_from:
                raise ValidationError("Los gastos requieren cuenta de origen.")
        elif self.kind == 'INGRESO':
            if not self.account_to:
                raise ValidationError("Los ingresos requieren cuenta de destino.")
        elif self.kind == 'TRANSFERENCIA':
            if not self.account_from or not self.account_to:
                raise ValidationError("Las transferencias requieren cuenta de origen y destino.")
        elif self.kind == 'PAGO_TARJETA':
            if not self.account_from or not self.account_to:
                raise ValidationError("Los pagos de tarjeta requieren cuenta de origen y destino.")

    def __str__(self):
        return f"Recurrente: {self.get_kind_display()} - {self.amount} {self.currency}"

    class Meta:
        verbose_name = "Transacción Recurrente"
        verbose_name_plural = "Transacciones Recurrentes"


class BudgetPlan(models.Model):
    FREQUENCIES = [
        ('SEMANAL', 'Semanal'),
        ('QUINCENAL', 'Quincenal'),
        ('MENSUAL', 'Mensual'),
    ]

    frequency = models.CharField(max_length=10, choices=FREQUENCIES)
    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(max_length=3, choices=Account.CURRENCIES, default='PEN')
    target_income = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    target_expenses = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    savings_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])

    @property
    def planned_net(self):
        return self.target_income - self.target_expenses

    @property
    def target_savings(self):
        return max(Decimal('0.00'), self.planned_net * (self.savings_rate / 100))

    def clean(self):
        if self.period_start >= self.period_end:
            raise ValidationError("La fecha de inicio debe ser anterior a la de fin.")
        if self.savings_rate > 100:
            raise ValidationError("La tasa de ahorro no puede exceder 100%.")

    def __str__(self):
        return f"Presupuesto {self.get_frequency_display()} - {self.period_start} a {self.period_end}"

    class Meta:
        verbose_name = "Plan de Presupuesto"
        verbose_name_plural = "Planes de Presupuesto"
