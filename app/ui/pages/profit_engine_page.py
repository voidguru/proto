"""
Profit Engine Page
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.ui.base_page import BasePage

class ProfitEnginePage(BasePage):

    def render(self):
        st.header("Profit Engine")

        # -----------------------------
        # LOAD DATA
        # -----------------------------
        df_income = pd.DataFrame(self.state.income_statement_df)
        df_fin = pd.DataFrame(self.state.financials_df)

        # Sort by date
        df_income.sort_values("date", inplace=True)
        df_fin.sort_values("date", inplace=True)

        latest_income = df_income.iloc[-1]
        latest_fin = df_fin.iloc[-1]

        st.write("### Revenue & Profitability Trends")

        # -----------------------------
        # TREND CHARTS
        # -----------------------------
        col1, col2 = st.columns(2)

        # Revenue Trend
        with col1:
            fig_rev = px.line(
                df_income,
                x="date",
                y="revenue",
                title="Revenue (5-Year Trend)",
                markers=True
            )
            st.plotly_chart(fig_rev, width='content')

        # Operating Income Trend
        with col2:
            fig_op = px.line(
                df_income,
                x="date",
                y="operatingIncome",
                title="Operating Income Trend",
                markers=True
            )
            st.plotly_chart(fig_op, width='content')

        # -----------------------------
        # MARGIN STACK (WATERFALL BAR)
        # -----------------------------
        st.write("### Margin Stack (Gross → Operating → Net)")

        margin_fig = go.Figure(data=[
            go.Bar(
                name="Gross Margin",
                x=df_fin["date"],
                y=df_fin["grossProfitMargin"] * 100
            ),
            go.Bar(
                name="Operating Margin",
                x=df_fin["date"],
                y=df_fin["operatingProfitMargin"] * 100
            ),
            go.Bar(
                name="Net Margin",
                x=df_fin["date"],
                y=df_fin["netProfitMargin"] * 100
            )
        ])
        margin_fig.update_layout(
            barmode='group',
            title="Margin Comparison Over Time (%)"
        )
        st.plotly_chart(margin_fig)

        # -----------------------------
        # OPERATIONAL EFFICIENCY
        # -----------------------------
        st.write("### Operational Efficiency Metrics")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Asset Turnover",
            f"{latest_fin['assetTurnover']:.2f}"
        )
        col2.metric(
            "Inventory Turnover",
            f"{latest_fin['inventoryTurnover']:.1f}x"
        )
        col3.metric(
            "Receivables Turnover",
            f"{latest_fin['receivablesTurnover']:.1f}x"
        )

        col4.metric(
            "Payables Turnover",
            f"{latest_fin['payablesTurnover']:.1f}x"
        )
        col5.metric(
            "Fixed Asset Turnover",
            f"{latest_fin['fixedAssetTurnover']:.1f}x"
        )

        st.write("---")

        # -----------------------------
        # UNIT ECONOMICS
        # -----------------------------
        st.write("### Unit Economics")

        latest_rev = latest_income["revenue"]
        latest_op = latest_income["operatingIncome"]
        latest_net = latest_income["netIncome"]

        unit1, unit2, unit3 = st.columns(3)

        unit1.metric(
            "Operating Income per $ Revenue",
            f"{(latest_op / latest_rev) * 100:.1f}%"
        )

        unit2.metric(
            "Net Income per $ Revenue",
            f"{(latest_net / latest_rev) * 100:.1f}%"
        )

        # FCF per revenue requires cashflow
        df_cash = pd.DataFrame(self.state.cashflow_df).sort_values("date")
        latest_cash = df_cash.iloc[-1]
        fcf_margin = latest_cash["freeCashFlow"] / latest_income["revenue"]

        unit3.metric(
            "Free Cash Flow per $ Revenue",
            f"{fcf_margin * 100:.1f}%"
        )

        st.write("---")

        # -----------------------------
        # INSIGHTS ENGINE
        # -----------------------------
        st.write("### Profit Engine Insights")

        insights = []

        # Margin expansion/contraction
        gm_now = latest_fin["grossProfitMargin"]
        gm_prev = df_fin.iloc[-2]["grossProfitMargin"]

        if gm_now > gm_prev:
            insights.append("• Gross margin expanded year-over-year.")
        else:
            insights.append("• Gross margin declined year-over-year.")

        # Operating leverage
        op_margin_now = latest_fin["operatingProfitMargin"]
        op_margin_prev = df_fin.iloc[-2]["operatingProfitMargin"]

        if op_margin_now > op_margin_prev:
            insights.append("• Operating margin improving — positive operating leverage.")
        else:
            insights.append("• Operating margin weakening — cost pressures increasing.")

        # Efficiency improvement
        inv_turn = latest_fin["inventoryTurnover"]
        inv_prev = df_fin.iloc[-2]["inventoryTurnover"]
        if inv_turn > inv_prev:
            insights.append("• Inventory turnover improved — better working capital efficiency.")

        # Revenue trend
        rev_now = df_income.iloc[-1]["revenue"]
        rev_prev = df_income.iloc[-2]["revenue"]
        rev_growth = (rev_now - rev_prev) / rev_prev

        if rev_growth > 0.05:
            insights.append("• Strong revenue acceleration (>5% YoY).")
        elif rev_growth < 0:
            insights.append("• Revenue contracted year-over-year.")

        # Display insights
        for item in insights:
            st.write(item)
