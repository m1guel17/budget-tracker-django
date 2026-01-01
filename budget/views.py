from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Sum, F, Case, When, Value, DecimalField, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Transaction, Account, Category, BudgetPlan, ExchangeRate, Payee
from django.contrib import messages

def get_exchange_rate(date):
    # Get the latest exchange rate on or before the date
    rate = ExchangeRate.objects.filter(date__lte=date).order_by('-date').first()
    return rate.usd_to_pen if rate else None

def convert_to_pen(amount, currency, date):
    if currency == 'PEN':
        return amount
    rate = get_exchange_rate(date)
    return amount * rate if rate else amount  # If no rate, return original

def dashboard(request):
    # Default period: current month
    today = timezone.now().date()
    start_date = today.replace(day=1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # KPIs
    transactions = Transaction.objects.filter(date__range=(start_date, end_date))

    # PEN
    pen_transactions = transactions.filter(currency='PEN')
    # pen_income = pen_transactions.filter(kind='INGRESO', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    # pen_expenses = pen_transactions.filter(kind='GASTO', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    pen_income = pen_transactions.filter(Q(kind='INGRESO') | Q(kind='TRANSFERENCIA_EXTERNA', account_to__isnull=False), is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    pen_expenses = pen_transactions.filter(Q(kind='GASTO') | Q(kind='TRANSFERENCIA_EXTERNA', account_from__isnull=False), is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    pen_savings = pen_income - pen_expenses
    pen_balance = sum(account.balance for account in Account.objects.filter(currency='PEN').exclude(type="CREDITO"))

    # USD
    usd_transactions = transactions.filter(currency='USD')
    # usd_income = usd_transactions.filter(kind='INGRESO', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    # usd_expenses = usd_transactions.filter(kind='GASTO', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    usd_income = usd_transactions.filter(Q(kind='INGRESO') | Q(kind='TRANSFERENCIA_EXTERNA', account_to__isnull=False), is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    usd_expenses = usd_transactions.filter(Q(kind='GASTO') | Q(kind='TRANSFERENCIA_EXTERNA', account_from__isnull=False), is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    usd_savings = usd_income - usd_expenses
    usd_balance = sum(account.balance for account in Account.objects.filter(currency='USD'))

    context = {
        'pen_income': pen_income,
        'pen_expenses': pen_expenses,
        'pen_savings': pen_savings,
        'pen_balance': pen_balance,
        'usd_income': usd_income,
        'usd_expenses': usd_expenses,
        'usd_savings': usd_savings,
        'usd_balance': usd_balance,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'dashboard.html', context)

def transactions(request):
    edit_transaction = None
    if 'edit' in request.GET:
        edit_transaction = get_object_or_404(Transaction, id=request.GET['edit'])

    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        if transaction_id:
            # Edit existing
            transaction = get_object_or_404(Transaction, id=transaction_id)
            transaction.kind = request.POST.get('kind')
            date_str = request.POST.get('date')
            transaction.date = datetime.fromisoformat(date_str).date()
            transaction.effective_period = transaction.date.replace(day=1)
            transaction.amount = request.POST.get('amount')
            transaction.currency = request.POST.get('currency')
            category_id = request.POST.get('category')
            transaction.category_id = category_id if category_id else None
            transaction.description = request.POST.get('description')
            transaction.payment_method = request.POST.get('payment_method')
            account_from_id = request.POST.get('account_from')
            transaction.account_from_id = account_from_id if account_from_id else None
            account_to_id = request.POST.get('account_to')
            transaction.account_to_id = account_to_id if account_to_id else None
            payee_name = request.POST.get('payee')
            if payee_name:
                payee, _ = Payee.objects.get_or_create(name=payee_name)
                transaction.payee = payee
            else:
                transaction.payee = None
            try:
                transaction.save()
                messages.success(request, 'Transacción actualizada exitosamente.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            # Create new
            kind = request.POST.get('kind')
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            currency = request.POST.get('currency')
            category_id = request.POST.get('category')
            description = request.POST.get('description')
            payment_method = request.POST.get('payment_method')
            account_from_id = request.POST.get('account_from')
            account_to_id = request.POST.get('account_to')
            payee_name = request.POST.get('payee')

            date_obj = datetime.fromisoformat(date).date()
            transaction = Transaction(
                kind=kind,
                date=date_obj,
                effective_period=date_obj.replace(day=1),
                amount=amount,
                currency=currency,
                description=description,
                payment_method=payment_method,
            )
            if category_id:
                transaction.category_id = category_id
            if account_from_id:
                transaction.account_from_id = account_from_id
            if account_to_id:
                transaction.account_to_id = account_to_id
            if payee_name:
                payee, _ = Payee.objects.get_or_create(name=payee_name)
                transaction.payee = payee
            try:
                transaction.save()
                messages.success(request, 'Transacción creada exitosamente.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        return redirect('transactions')

    transactions = Transaction.objects.filter(date__gte='2025-01-01').order_by('-date')
    categories = Category.objects.filter(is_active=True)
    accounts = Account.objects.all()
    payees = Payee.objects.all()
    return render(request, 'transactions.html', {
        'transactions': transactions,
        'categories': categories,
        'accounts': accounts,
        'payees': payees,
        'edit_transaction': edit_transaction,
    })

def accounts(request):
    edit_account = None
    if 'edit' in request.GET:
        edit_account = get_object_or_404(Account, id=request.GET['edit'])

    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        if account_id:
            # Edit existing
            account = get_object_or_404(Account, id=account_id)
            account.name = request.POST.get('name')
            account.type = request.POST.get('type')
            account.currency = request.POST.get('currency', 'PEN')
            account.opening_balance = request.POST.get('opening_balance', '0.00')
            account.credit_limit = request.POST.get('credit_limit') if account.type == 'CREDITO' else None
            account.billing_cycle_day = request.POST.get('billing_cycle_day') if account.type == 'CREDITO' else None
            account.due_day = request.POST.get('due_day') if account.type == 'CREDITO' else None
            account.savings_amount = request.POST.get('savings_amount') if account.type == 'DEBITO' else None
            try:
                account.save()
                messages.success(request, 'Cuenta actualizada exitosamente.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            # Create new
            name = request.POST.get('name')
            type = request.POST.get('type')
            currency = request.POST.get('currency', 'PEN')
            opening_balance = request.POST.get('opening_balance', '0.00')
            credit_limit = request.POST.get('credit_limit') if type == 'CREDITO' else None
            billing_cycle_day = request.POST.get('billing_cycle_day') if type == 'CREDITO' else None
            due_day = request.POST.get('due_day') if type == 'CREDITO' else None
            savings_amount = request.POST.get('savings_amount') if type == 'DEBITO' else None

            account = Account(
                name=name,
                type=type,
                currency=currency,
                opening_balance=opening_balance,
                credit_limit=credit_limit,
                billing_cycle_day=billing_cycle_day,
                due_day=due_day,
                savings_amount=savings_amount,
            )
            try:
                account.save()
                messages.success(request, 'Cuenta creada exitosamente.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        return redirect('accounts')

    accounts = Account.objects.all()
    return render(request, 'accounts.html', {'accounts': accounts, 'edit_account': edit_account})

def budgets(request):
    if request.method == 'POST':
        frequency = request.POST.get('frequency')
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        currency = request.POST.get('currency', 'PEN')
        target_income = request.POST.get('target_income')
        target_expenses = request.POST.get('target_expenses')
        savings_rate = request.POST.get('savings_rate')

        budget = BudgetPlan(
            frequency=frequency,
            period_start=period_start,
            period_end=period_end,
            currency=currency,
            target_income=target_income,
            target_expenses=target_expenses,
            savings_rate=savings_rate,
        )
        try:
            budget.save()
            messages.success(request, 'Presupuesto creado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('budgets')

    budgets = BudgetPlan.objects.all()
    return render(request, 'budgets.html', {'budgets': budgets})

def exchange_rates(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        usd_to_pen = request.POST.get('usd_to_pen')

        rate, created = ExchangeRate.objects.get_or_create(date=date, defaults={'usd_to_pen': usd_to_pen})
        if not created:
            rate.usd_to_pen = usd_to_pen
            rate.save()
        messages.success(request, 'Tipo de cambio guardado exitosamente.')
        return redirect('exchange_rates')

    rates = ExchangeRate.objects.all().order_by('-date')
    return render(request, 'exchange_rates.html', {'rates': rates})

# API views
def api_dashboard_summary(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    if not start or not end:
        return JsonResponse({'error': 'start and end required'}, status=400)
    start_date = datetime.fromisoformat(start).date()
    end_date = datetime.fromisoformat(end).date()

    transactions = Transaction.objects.filter(date__range=(start_date, end_date), is_valid=True)

    pen_income = transactions.filter(currency='PEN', kind='INGRESO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    pen_expenses = transactions.filter(currency='PEN', kind='GASTO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    usd_income = transactions.filter(currency='USD', kind='INGRESO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    usd_expenses = transactions.filter(currency='USD', kind='GASTO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    return JsonResponse({
        'pen_income': float(pen_income),
        'pen_expenses': float(pen_expenses),
        'usd_income': float(usd_income),
        'usd_expenses': float(usd_expenses),
    })

def api_dashboard_netflow_12m(request):
    # Last 12 months net flow (income - expenses) per month, chronological order
    today = timezone.now().date()
    data = []
    for i in range(11, -1, -1):  # From 11 to 0, oldest to newest
        month_start = (today - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        transactions = Transaction.objects.filter(date__range=(month_start, month_end), is_valid=True)
        
        # pen_income = transactions.filter(Q(kind='INGRESO', payment_method='TRANSFERENCIA') | Q(kind='TRANSFERENCIA_EXTERNA', account_to__isnull=False), currency='PEN', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pen_income = transactions.filter(Q(kind='INGRESO') | Q(kind='TRANSFERENCIA_EXTERNA', account_to__isnull=False), currency='PEN', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        # pen_expense = transactions.filter(Q(kind='GASTO', payment_method='TRANSFERENCIA') | Q(kind='TRANSFERENCIA_EXTERNA', account_from__isnull=False), currency='PEN', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pen_expense = transactions.filter(Q(kind='GASTO') | Q(kind='TRANSFERENCIA_EXTERNA', account_from__isnull=False), currency='PEN', is_valid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pen_net = pen_income - pen_expense
        # pen_income_transf = transactions.filter(currency='PEN', kind='TRANSFERENCIA_EXTERNA').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        # pen_expense_transf = transactions.filter(currency='PEN', kind='TRANSFERENCIA_EXTERNA').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        # pen_net = pen_income + pen_income_transf - pen_expense - pen_expense_transf
        
        usd_income = transactions.filter(currency='USD', kind='INGRESO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        usd_expense = transactions.filter(currency='USD', kind='GASTO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        usd_net = usd_income - usd_expense
        data.append({
            'month': month_start.strftime('%Y-%m'),
            'pen': float(pen_net),
            'usd': float(usd_net),
        })
    # print(data)
    return JsonResponse(data, safe=False)

def api_dashboard_income_expenses_12m(request):
    # Last 12 months income and expenses per month, chronological order
    today = timezone.now().date()
    data = []
    for i in range(11, -1, -1):  # From 11 to 0, oldest to newest
        month_start = (today - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        transactions = Transaction.objects.filter(date__range=(month_start, month_end))
        pen_income = transactions.filter(currency='PEN', kind='INGRESO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pen_expense = transactions.filter(currency='PEN', kind='GASTO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        usd_income = transactions.filter(currency='USD', kind='INGRESO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        usd_expense = transactions.filter(currency='USD', kind='GASTO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        data.append({
            'month': month_start.strftime('%Y-%m'),
            'pen_income': float(pen_income),
            'pen_expense': float(pen_expense),
            'usd_income': float(usd_income),
            'usd_expense': float(usd_expense),
        })
    # print(data)
    return JsonResponse(data, safe=False)

def invalidate_transaction(request, transaction_id):
    if request.method == 'POST':
        transaction = get_object_or_404(Transaction, id=transaction_id)
        if transaction.is_valid:
            transaction.is_valid = False
            transaction.save()
            messages.success(request, 'Transacción invalidada exitosamente.')
        else:
            messages.warning(request, 'La transacción ya está invalidada.')
    return redirect('transactions')

def delete_transaction(request, transaction_id):
    if request.method == 'POST':
        transaction = get_object_or_404(Transaction, id=transaction_id)
        if not transaction.is_valid:
            transaction.delete()
            messages.success(request, 'Transacción eliminada permanentemente.')
        else:
            messages.error(request, 'Solo se pueden eliminar transacciones invalidas.')
    return redirect('transactions')

def api_dashboard_expenses_by_category(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    mode = request.GET.get('mode', 'original')  # original or pen
    if not start or not end:
        return JsonResponse({'error': 'start and end required'}, status=400)
    start_date = datetime.fromisoformat(start).date()
    end_date = datetime.fromisoformat(end).date()

    expenses = Transaction.objects.filter(date__range=(start_date, end_date), kind='GASTO', is_valid=True)
    data = {}
    for exp in expenses:
        amount = exp.amount if mode == 'original' else convert_to_pen(exp.amount, exp.currency, exp.date)
        cat = exp.category.name if exp.category else 'Sin Categoría'
        data[cat] = data.get(cat, Decimal('0.00')) + amount
    return JsonResponse({k: float(v) for k, v in data.items()})

def api_dashboard_actual_vs_budget(request):
    budget_id = request.GET.get('budget_id')
    if not budget_id:
        return JsonResponse({'error': 'budget_id required'}, status=400)
    budget = get_object_or_404(BudgetPlan, id=budget_id)

    transactions = Transaction.objects.filter(effective_period=budget.period_start.replace(day=1), is_valid=True)
    actual_income = transactions.filter(kind='INGRESO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    actual_expenses = transactions.filter(kind='GASTO').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    actual_savings = actual_income - actual_expenses

    return JsonResponse({
        'target_income': float(budget.target_income),
        'actual_income': float(actual_income),
        'target_expenses': float(budget.target_expenses),
        'actual_expenses': float(actual_expenses),
        'target_savings': float(budget.target_savings),
        'actual_savings': float(actual_savings),
    })
