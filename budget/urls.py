from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transacciones/', views.transactions, name='transactions'),
    path('transacciones/invalidar/<int:transaction_id>/', views.invalidate_transaction, name='invalidate_transaction'),
    path('transacciones/eliminar/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('cuentas/', views.accounts, name='accounts'),
    path('presupuestos/', views.budgets, name='budgets'),
    path('tipo-cambio/', views.exchange_rates, name='exchange_rates'),
    # API
    path('api/dashboard/summary', views.api_dashboard_summary, name='api_dashboard_summary'),
    path('api/dashboard/netflow_12m', views.api_dashboard_netflow_12m, name='api_dashboard_netflow_12m'),
    path('api/dashboard/income_expenses_12m', views.api_dashboard_income_expenses_12m, name='api_dashboard_income_expenses_12m'),
    path('api/dashboard/expenses_by_category', views.api_dashboard_expenses_by_category, name='api_dashboard_expenses_by_category'),
    path('api/dashboard/actual_vs_budget', views.api_dashboard_actual_vs_budget, name='api_dashboard_actual_vs_budget'),
]