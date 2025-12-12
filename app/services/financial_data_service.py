"""
Service layer for handling financial data processing.
This service encapsulates the business logic for fetching, caching,
and preparing financial data for the UI layer.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import json
from pydantic import ValidationError
from app.repositories.financial_data_repository import FinancialDataRepository
from app.core.models import BalanceSheet, IncomeStatement, CashFlowStatement, KeyMetrics, Ratios
from decimal import Decimal

class FinancialDataService:
    def __init__(self, repository: FinancialDataRepository):
        self.repository = repository

    def get_financial_statements(self, symbol: str, limit: int = 5) -> Tuple[List[BalanceSheet], List[IncomeStatement], List[CashFlowStatement], List[KeyMetrics], List[Ratios]]:
        """
        Fetches all financial statements for a given symbol.
        """
        bs = self.repository.load(symbol, "balance-sheet-statement", BalanceSheet, limit)
        is_ = self.repository.load(symbol, "income-statement", IncomeStatement, limit)
        cf = self.repository.load(symbol, "cash-flow-statement", CashFlowStatement, limit)
        metrics = self.repository.load(symbol, "key-metrics", KeyMetrics, limit)
        financial = self.repository.load(symbol, "ratios", Ratios, limit)
        return bs, is_, cf, metrics, financial

    def convert_to_dataframes(self, bs_models: List[BalanceSheet], is_models: List[IncomeStatement], cf_models: List[CashFlowStatement], key_metrics_models: List[KeyMetrics], financeial_metrics_models: List[Ratios]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Converts lists of Pydantic models to pandas DataFrames.
        """
        df_bs = pd.DataFrame([m.dict() for m in bs_models])
        df_is = pd.DataFrame([m.dict() for m in is_models])
        df_cf = pd.DataFrame([m.dict() for m in cf_models])
        df_km = pd.DataFrame([m.dict() for m in key_metrics_models])
        df_fm = pd.DataFrame([m.dict() for m in financeial_metrics_models])

        df_bs = df_bs.sort_values("date", ascending=False)
        df_is = df_is.sort_values("date", ascending=False)
        df_cf = df_cf.sort_values("date", ascending=False)
        df_km = df_km.sort_values("date", ascending=False)
        df_fm = df_fm.sort_values("date", ascending=False)

        return df_bs, df_is, df_cf, df_km, df_fm

    def load_mock_data(self, json_path: str) -> Tuple[List[BalanceSheet], List[IncomeStatement], List[CashFlowStatement], List[KeyMetrics]]:
        """
        Loads mock data from a JSON file.
        """
        with open(json_path, "r") as f:
            raw = json.load(f)

        # Parse balance sheet
        bs_models = []
        for entry in raw["balance_sheet"]:
            try:
                bs_models.append(BalanceSheet(**entry))
            except ValidationError as e:
                print("❌ BalanceSheet validation error:", e)

        # Parse income statement
        is_models = []
        for entry in raw["income_statement"]:
            try:
                is_models.append(IncomeStatement(**entry))
            except ValidationError as e:
                print("❌ IncomeStatement validation error:", e)

        # Parse cash flow statement
        cf_models = []
        for entry in raw["cashflow_statement"]:
            try:
                cf_models.append(CashFlowStatement(**entry))
            except ValidationError as e:
                print("❌ CashFlow validation error:", e)

        # Parse cash flow statement
        metrics_models = []
        for entry in raw["metrics"]:
            try:
                metrics_models.append(KeyMetrics(**entry))
            except ValidationError as e:
                print("❌ CashFlow validation error:", e)

        # Parse cash flow statement
        financials_models = []
        for entry in raw["financial_metrics"]:
            try:
                financials_models.append(Ratios(**entry))
            except ValidationError as e:
                print("❌ CashFlow validation error:", e)

        return bs_models, is_models, cf_models, metrics_models, financials_models

    # def compute_metrics(self, income: pd.DataFrame, balance: pd.DataFrame, cashflow: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    #     """
    #     Computes derived financial metrics from the base statements.
    #     """
    #     if income.empty or balance.empty or cashflow.empty:
    #         return pd.DataFrame()

    #     # Standardize fiscalYear column
    #     for df in [income, balance, cashflow, metrics]:
    #         for c in ['fiscalYear', 'fiscal_year', 'year', 'fy', 'Period']:
    #             if c in df.columns:
    #                 df['fiscalYear'] = df[c]
    #                 break

    #     # Merge dataframes
    #     out = income.merge(balance, on='fiscalYear', how='outer')
    #     out = out.merge(cashflow, on='fiscalYear', how='outer')
    #     out = out.merge(metrics, on='fiscalYear', how='outer')

    #     # Derived metrics
    #     out['netDebt'] = (out['shortTermDebt'].fillna(0) + out['longTermDebt'].fillna(0)) - out['cashAndCashEquivalents'].fillna(0)
    #     out['buybacks'] = -out['commonStockRepurchased'].fillna(0)
    #     out['dividends'] = -out['commonDividendsPaid'].fillna(0)

    #     # Ratios
    #     out['OCF_to_NetIncome'] = out['operatingCashFlow'] / out['netIncome']
    #     out['FCF_to_NetIncome'] = out['freeCashFlow'] / out['netIncome']
    #     out['capex_to_revenue'] = out['capitalExpenditure'] / out['revenue']
    #     out['buyback_pct_of_FCF'] = out['buybacks'] / out['freeCashFlow']
    #     out['dividend_pct_of_FCF'] = out['dividends'] / out['freeCashFlow']
    #     out['payout_pct_of_FCF'] = (out['buybacks'] + out['dividends']) / out['freeCashFlow']
    #     out['current_ratio'] = out['totalAssets'] / out['totalLiabilities']
    #     out['debt_to_equity'] = ((out['shortTermDebt'].fillna(0) + out['longTermDebt'].fillna(0)) / out['totalStockholdersEquity'])

    #     out = out.replace([np.inf, -np.inf], np.nan)
    #     return out.reset_index()

    def format_b(self, x: float) -> str:
        """Formats a number in billions."""
        try:
            return f"${x / 1e9:,.2f}B"
        except (TypeError, ValueError):
            return str(x)
