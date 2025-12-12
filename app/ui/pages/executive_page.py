"""
Executive Summary Page
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from decimal import Decimal
from app.ui.base_page import BasePage

class ExecutivePage(BasePage):

    def render(self):
        st.header("Executive Overview")

        # ----------------------------------------
        # LOAD DATA
        # ----------------------------------------
        df_income = self.state.income_statement_df
        df_cash = self.state.cashflow_df
        df_metrics = self.state.metrics_df

        # Convert to DataFrame if needed
        df_income = pd.DataFrame(df_income)
        df_cash = pd.DataFrame(df_cash)
        df_metrics = pd.DataFrame(df_metrics)

        # Sort by date
        df_income.sort_values("date", inplace=True)
        df_cash.sort_values("date", inplace=True)
        df_metrics.sort_values("date", inplace=True)

        # Latest values
        latest_income = df_income.iloc[-1]
        latest_cash = df_cash.iloc[-1]
        latest_metrics = df_metrics.iloc[-1]

        # ----------------------------------------
        # TOP KPI BAR
        # ----------------------------------------
        st.subheader("Key Performance Indicators")

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        kpi1.metric(
            "Market Cap",
            f"${latest_metrics['marketCap'] / Decimal(1e9):,.1f}B"
        )

        kpi2.metric(
            "Revenue (FY)",
            f"${latest_income['revenue'] / Decimal(1e9):,.1f}B"
        )

        kpi3.metric(
            "Net Income",
            f"${latest_income['netIncome'] / Decimal(1e9):,.1f}B"
        )

        kpi4.metric(
            "Free Cash Flow",
            f"${latest_cash['freeCashFlow'] / Decimal(1e9):,.1f}B"
        )

        st.write("---")

        # ----------------------------------------
        # CORE TREND CHARTS
        # ----------------------------------------
        st.subheader("Performance Trends (5-Year)")

        col1, col2, col3 = st.columns(3)

        # Revenue trend
        # with col1:
        fig_rev = px.line(
            df_income,
            x="date",
            y=["revenue", "operatingIncome"],
            title="Revenue"
        )
        st.plotly_chart(fig_rev, )
        fig_op = px.line(
            df_income,
            x="date",
            y="operatingIncome",
            title="Operating Income"
        )
        st.plotly_chart(fig_op, )
        fig_fcf = px.line(
            df_cash,
            x="date",
            y="freeCashFlow",
            title="Free Cash Flow"
        )
        st.plotly_chart(fig_fcf, )
        # Operating income trend
        # with col2:
        #     fig_op = px.line(
        #         df_income,
        #         x="date",
        #         y="operatingIncome",
        #         title="Operating Income"
        #     )
        #     st.plotly_chart(fig_op, )

        # # FCF trend
        # with col3:
        #     fig_fcf = px.line(
        #         df_cash,
        #         x="date",
        #         y="freeCashFlow",
        #         title="Free Cash Flow"
        #     )
        #     st.plotly_chart(fig_fcf, )

        st.write("---")

        # ----------------------------------------
        # PROFITABILITY & CASH QUALITY
        # ----------------------------------------
        st.subheader("Profitability & Cash Quality")

        m1, m2, m3 = st.columns(3)

        m1.metric(
            "Net Profit Margin",
            f"{latest_income['netIncome'] / latest_income['revenue'] * 100:.1f}%"
        )

        fcf_margin = latest_cash["freeCashFlow"] / latest_income["revenue"]
        m2.metric(
            "Free Cash Flow Margin",
            f"{fcf_margin * 100:.1f}%"
        )

        income_quality = latest_cash["operatingCashFlow"] / latest_income["netIncome"]
        m3.metric(
            "Income Quality (CFO / Net Income)",
            f"{income_quality:.2f}"
        )

        st.write("---")

        # ----------------------------------------
        # EXECUTIVE INSIGHTS (Auto-generated)
        # ----------------------------------------
        st.subheader("Executive Insights")

        insights = []

        # Insight: Income quality
        if income_quality > 1.1:
            insights.append("• Strong cash-backed earnings (high income quality).")
        elif income_quality < 0.9:
            insights.append("• Earnings quality weakening (CFO < Net Income).")

        # Insight: FCF margin
        if fcf_margin > 0.20:
            insights.append("• Excellent free cash flow generation.")
        elif fcf_margin < 0.10:
            insights.append("• Weak FCF margins; investigate capex or WC changes.")

        # Trend-based revenue insight
        rev_growth = (
            df_income.iloc[-1]["revenue"] - df_income.iloc[-2]["revenue"]
        ) / df_income.iloc[-2]["revenue"]

        if rev_growth > 0.03:
            insights.append("• Revenue growth accelerating year-over-year.")
        elif rev_growth < 0:
            insights.append("• Revenue contracted last year.")

        # Cash conversion cycle
        ccc = latest_metrics.get("cashConversionCycle")
        if ccc is not None:
            if ccc < 0:
                insights.append("• Negative cash conversion cycle — strong supplier power.")
            elif ccc > 20:
                insights.append("• Long cash conversion cycle — potential liquidity drag.")

        # Display insights
        if len(insights) == 0:
            st.info("No significant insights detected.")
        else:
            for item in insights:
                st.write(item)
