"""
Unit tests for the FinancialDataService.
"""
import pandas as pd
import pytest
from app.services.financial_data_service import FinancialDataService
from app.repositories.financial_data_repository import FinancialDataRepository
from decimal import Decimal

@pytest.fixture
def financial_data_service():
    """
    Provides a FinancialDataService instance for testing.
    """
    return FinancialDataService(None)

def test_compute_metrics(financial_data_service):
    """
    Tests the compute_metrics method of the FinancialDataService.
    """
    income_df = pd.DataFrame({
        'fiscalYear': [2023],
        'revenue': [Decimal('1000')],
        'netIncome': [Decimal('100')],
        'operatingCashFlow': [Decimal('200')],
        'capitalExpenditure': [Decimal('50')],
        'freeCashFlow': [Decimal('150')],
        'grossProfit': [Decimal('400')],
        'operatingIncome': [Decimal('300')],
        'commonStockRepurchased': [Decimal('20')],
        'commonDividendsPaid': [Decimal('10')],
    })
    balance_df = pd.DataFrame({
        'fiscalYear': [2023],
        'totalAssets': [Decimal('1000')],
        'totalLiabilities': [Decimal('500')],
        'shortTermDebt': [Decimal('100')],
        'longTermDebt': [Decimal('200')],
        'cashAndCashEquivalents': [Decimal('50')],
        'totalStockholdersEquity': [Decimal('500')],
    })
    cashflow_df = pd.DataFrame({
        'fiscalYear': [2023],
    })
    metrics_df = pd.DataFrame({
        'fiscalYear': [2023],
    })

    result = financial_data_service.compute_metrics(income_df, balance_df, cashflow_df, metrics_df)

    assert not result.empty
    assert result['netDebt'][0] == Decimal('250')
    assert result['buybacks'][0] == Decimal('-20')
    assert result['dividends'][0] == Decimal('-10')
    assert result['OCF_to_NetIncome'][0] == Decimal('2.0')
    assert result['FCF_to_NetIncome'][0] == Decimal('1.5')
    assert result['capex_to_revenue'][0] == Decimal('0.05')
    assert result['payout_pct_of_FCF'][0] == (Decimal('-30') / Decimal('150'))
    assert result['current_ratio'][0] == Decimal('2.0')
    assert result['debt_to_equity'][0] == Decimal('0.6')
