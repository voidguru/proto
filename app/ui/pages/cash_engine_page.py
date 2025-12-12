"""
Cash Engine Page
"""
from decimal import Decimal
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.ui.base_page import BasePage

class CashEnginePage(BasePage):

    def render(self):
        st.header("Cash Engine")

        # --------------------------------
        # LOAD DATA
        # --------------------------------
        df_cash = pd.DataFrame(self.state.cashflow_df)
        df_income = pd.DataFrame(self.state.income_statement_df)
        df_metrics = pd.DataFrame(self.state.metrics_df)

        df_cash.sort_values("date", inplace=True)
        df_income.sort_values("date", inplace=True)
        df_metrics.sort_values("date", inplace=True)

        latest_cash = df_cash.iloc[-1]
        latest_income = df_income.iloc[-1]
        latest_metrics = df_metrics.iloc[-1]

        # --------------------------------
        # TOP KPI BAR
        # --------------------------------
        st.subheader("Key Cash Flow Metrics")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Operating Cash Flow",
            f"${latest_cash['operatingCashFlow'] / Decimal(1e9):,.1f}B"
        )

        c2.metric(
            "Free Cash Flow",
            f"${latest_cash['freeCashFlow'] / Decimal(1e9):,.1f}B"
        )

        fcf_margin = latest_cash["freeCashFlow"] / latest_income["revenue"]
        c3.metric(
            "FCF Margin",
            f"{fcf_margin * 100:.1f}%"
        )

        income_quality = latest_cash["operatingCashFlow"] / latest_income["netIncome"]
        c4.metric(
            "Income Quality",
            f"{income_quality:.2f}"
        )

        st.write("---")

        # --------------------------------
        # CASH FLOW COMPOSITION (CFO / CFI / CFF)
        # --------------------------------
        st.subheader("Cash Flow Composition (CFO / CFI / CFF)")

        # Calculate CFI and CFF because data does not contain them aggregated
        df_cash["CFI"] = (
            df_cash["capitalExpenditure"]
            + df_cash.get("acquisitionsNet", 0)
            + df_cash.get("purchaseOfInvestment", 0)
            + df_cash.get("saleOfInvestment", 0)
            + df_cash.get("otherInvestingActivites", 0)
        )

        df_cash["CFF"] = (
            df_cash.get("debtRepayment", 0)
            + df_cash.get("commonStockRepurchased", 0)
            + df_cash.get("commonStockIssued", 0)
            + df_cash.get("dividendPaid", 0)
            + df_cash.get("otherFinancingActivities", 0)
        )

        fig_cf = go.Figure()

        fig_cf.add_trace(go.Bar(
            x=df_cash["date"],
            y=df_cash["operatingCashFlow"],
            name="Operating Cash Flow (CFO)"
        ))

        fig_cf.add_trace(go.Bar(
            x=df_cash["date"],
            y=df_cash["CFI"],
            name="Investing Cash Flow (CFI)"
        ))

        fig_cf.add_trace(go.Bar(
            x=df_cash["date"],
            y=df_cash["CFF"],
            name="Financing Cash Flow (CFF)"
        ))

        fig_cf.update_layout(
            title="Cash Flow Breakdown: CFO vs CFI vs CFF",
            barmode='group',
            legend_title="Cash Flow Type"
        )

        st.plotly_chart(fig_cf)


        st.write("---")

        # --------------------------------
        # FCF TREND CHART
        # --------------------------------
        st.subheader("Free Cash Flow Trend")

        fig_fcf = px.line(
            df_cash,
            x="date",
            y="freeCashFlow",
            markers=True,
            title="Free Cash Flow (5-Year Trend)"
        )
        st.plotly_chart(fig_fcf)

        st.write("---")

        # --------------------------------
        # CAPEX ANALYSIS
        # --------------------------------
        st.subheader("Capex & Investment")

        colA, colB, colC = st.columns(3)

        colA.metric(
            "Capital Expenditure",
            f"${latest_cash['capitalExpenditure'] / Decimal(1e9):,.2f}B"
        )

        capex_intensity = abs(latest_cash["capitalExpenditure"]) / latest_cash["operatingCashFlow"]
        colB.metric(
            "Capex as % of OCF",
            f"{capex_intensity * 100:.1f}%"
        )

        colC.metric(
            "Capex as % of Revenue",
            f"{abs(latest_cash['capitalExpenditure']) / latest_income['revenue'] * 100:.1f}%"
        )

        # Capex trend chart
        fig_capex = px.bar(
            df_cash,
            x="date",
            y="capitalExpenditure",
            title="Capital Expenditure Over Time"
        )
        st.plotly_chart(fig_capex)

        st.write("---")

        # --------------------------------
        # CASH CONVERSION CYCLE (IF AVAILABLE)
        # --------------------------------
        st.subheader("Cash Conversion Cycle")

        if "cashConversionCycle" in df_metrics.columns:
            fig_ccc = px.line(
                df_metrics,
                x="date",
                y="cashConversionCycle",
                title="Cash Conversion Cycle (Days)",
                markers=True
            )
            st.plotly_chart(fig_ccc)

            ccc_now = latest_metrics["cashConversionCycle"]
            st.metric("Current Cash Conversion Cycle", f"{ccc_now:.1f} days")

        else:
            st.info("No Cash Conversion Cycle data available.")

        st.write("---")

        # --------------------------------
        # INSIGHTS ENGINE
        # --------------------------------
        st.subheader("Cash Engine Insights")

        insights = []

        # Income quality
        if income_quality > 1.1:
            insights.append("• Strong earnings quality — cash flow exceeds net income.")
        elif income_quality < 0.9:
            insights.append("• Weak earnings quality — net income not fully backed by cash.")

        # FCF margin
        if fcf_margin > 0.25:
            insights.append("• Exceptional free cash flow margin.")
        elif fcf_margin < 0.10:
            insights.append("• Low FCF margin — capex or WC may be consuming cash.")

        # Capex trend
        if df_cash["capitalExpenditure"].iloc[-1] < df_cash["capitalExpenditure"].iloc[-2]:
            insights.append("• Capex declined year-over-year.")
        else:
            insights.append("• Capex rising — company may be investing aggressively.")

        # CFO trend
        ocf_now = df_cash.iloc[-1]["operatingCashFlow"]
        ocf_prev = df_cash.iloc[-2]["operatingCashFlow"]
        if ocf_now > ocf_prev:
            insights.append("• Operating cash flow improved year-over-year.")
        else:
            insights.append("• Operating cash flow declined — may indicate margin pressure.")

        # CCC insight
        if "cashConversionCycle" in df_metrics.columns:
            ccc = latest_metrics["cashConversionCycle"]
            if ccc < 0:
                insights.append("• Negative cash conversion cycle — strong supplier payment terms.")
            elif ccc > 20:
                insights.append("• Long cash conversion cycle — operational liquidity risk.")

        # Display insights
        for item in insights:
            st.write(item)
