"""
Capital Allocation Page
"""
from decimal import Decimal
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.ui.base_page import BasePage


class CapitalAllocationPage(BasePage):

    def render(self):
        st.header("Capital Allocation")

        # --------------------------------
        # Load Data
        # --------------------------------
        df_cash = self.state.cashflow_df.sort_values("date")
        df_income = self.state.income_statement_df.sort_values("date")
        df_metrics = self.state.metrics_df.sort_values("date")
        df_fin = self.state.financials_df.sort_values("date")
        df_bs = self.state.balance_sheet_df.sort_values("date")

        if df_cash.empty:
            st.warning("No cash flow data available for Capital Allocation analysis.")
            return

        latest_cash = df_cash.iloc[-1]
        latest_income = df_income.iloc[-1] if not df_income.empty else pd.Series()
        latest_fin = df_fin.iloc[-1] if not df_fin.empty else pd.Series()
        latest_bs = df_bs.iloc[-1] if not df_bs.empty else pd.Series()

        # --------------------------------
        # Shareholder Returns (Dividends + Buybacks)
        # --------------------------------

        df_cf = self.state.cashflow_df
        df_cf = df_cf.sort_values("date")


        # Build normalized columns
        df_cf["capex"] = df_cf["capitalExpenditure"]  # reinvestment
        df_cf["acquisitions"] = df_cf["acquisitionsNet"]

        # Investment rotation = purchases & sales of investments
        df_cf["investment_rotation"] = (
            df_cf["purchasesOfInvestments"]
            + df_cf["salesMaturitiesOfInvestments"]
            + df_cf["otherInvestingActivities"]
        )

        # Debt activity
        df_cf["debt_activity"] = df_cf["netDebtIssuance"]

        # Shareholder returns
        df_cf["buybacks"] = df_cf["commonStockRepurchased"]
        df_cf["dividends"] = df_cf.get("netDividendsPaid", 0)

        # Other financing
        df_cf["other_financing"] = df_cf["otherFinancingActivities"]

        categories = {
            "Reinvestment (CAPEX)": "capex",
            "Acquisitions": "acquisitions",
            "Investment Rotation": "investment_rotation",
            "Debt Activity": "debt_activity",
            "Buybacks": "buybacks",
            "Dividends": "dividends",
            "Other Financing": "other_financing",
        }

        fig = go.Figure()

        for label, col in categories.items():
            fig.add_trace(go.Bar(
                x=df_cf["date"],
                y=df_cf[col],
                name=label
            ))

        fig.update_layout(
            title="Capital Allocation Over Time",
            barmode="relative",
            legend_title="Capital Allocation Category"
        )

        st.plotly_chart(fig)

        st.write("""
        **Interpretation Guide**
        - Negative CAPEX → reinvestment in the business  
        - Negative buybacks → cash outflow to repurchase shares  
        - Negative dividends → cash returned to shareholders  
        - Positive debt issuance → borrowing cash  
        - Negative debt issuance → paying down debt  
        - Investment rotation → inflow/outflow from the securities portfolio  
        """)
        buybacks = latest_cash["commonStockRepurchased"]
        # dividends = latest_cash["dividendPaid"]
        # issuance = latest_cash["commonStockIssued"]

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Share Repurchases (Latest FY)",
            f"${abs(buybacks) / Decimal(1e9):,.2f}B" if not pd.isna(buybacks) else "n/a"
        )

        # c2.metric(
        #     "Dividends Paid (Latest FY)",
        #     f"${abs(dividends) / Decimal(1e9):,.2f}B" if not pd.isna(dividends) else "n/a"
        # )

        # c3.metric(
        #     "Net Stock Issuance",
        #     f"${issuance / Decimal(1e9):,.2f}B" if not pd.isna(issuance) else "n/a"
        # )

        # Buyback trend
        fig_buyback = px.bar(
            df_cash,
            x="date",
            y="commonStockRepurchased",
            title="Share Repurchases Over Time"
        )
        st.plotly_chart(fig_buyback)

        # Dividend trend
        # if "dividendPaid" in df_cash.columns:
        #     fig_div = px.bar(
        #         df_cash,
        #         x="date",
        #         y="dividendPaid",
        #         title="Dividends Paid Over Time"
        #     )
        #     st.plotly_chart(fig_div)

        st.write("---")

        # --------------------------------
        # Debt Policy & Capital Structure
        # --------------------------------
        st.subheader("Debt & Capital Structure")

        debt_repayment = latest_cash.get("debtRepayment", np.nan)
        long_term_debt = latest_bs.get("longTermDebt", np.nan)
        short_term_debt = latest_bs.get("shortTermDebt", np.nan)
        total_debt = (long_term_debt if not pd.isna(long_term_debt) else 0) + (short_term_debt if not pd.isna(short_term_debt) else 0)

        colA, colB, colC = st.columns(3)

        colA.metric(
            "Debt Repayments (Latest FY)",
            f"${abs(debt_repayment) / Decimal(1e9):,.2f}B" if not pd.isna(debt_repayment) else "n/a"
        )

        colB.metric(
            "Total Debt",
            f"${total_debt / Decimal(1e9):,.2f}B" if total_debt > 0 else "n/a"
        )

        # Debt ratios
        debt_to_equity = latest_fin.get("debtToEquityRatio", np.nan)
        colC.metric(
            "Debt-to-Equity",
            f"{debt_to_equity:.2f}x" if not pd.isna(debt_to_equity) else "n/a"
        )

        # Debt movement chart
        if "debtRepayment" in df_cash.columns:
            fig_debt = px.bar(
                df_cash,
                x="date",
                y="debtRepayment",
                title="Debt Repayments Over Time"
            )
            st.plotly_chart(fig_debt)

        st.write("---")

        # --------------------------------
        # FCF Allocation Breakdown (Capital Deployment)
        # --------------------------------
        st.subheader("Free Cash Flow Allocation")

        df_alloc = df_cash.copy()

        # Compute FCF explicitly
        df_alloc["FCF"] = df_alloc.get("freeCashFlow", np.nan)

        # Key deployment categories
        df_alloc["CapEx"] = df_alloc.get("capitalExpenditure", 0)
        df_alloc["Buybacks"] = df_alloc.get("commonStockRepurchased", 0)
        df_alloc["Dividends"] = df_alloc.get("dividendPaidAndCapexCoverageRatio", 0)
        df_alloc["DebtRepay"] = df_alloc.get("netDebtIssuance", 0)
        df_alloc["Acquisitions"] = df_alloc.get("acquisitionsNet", 0)

        # Pie chart for latest year
        alloc_latest = {
            "CapEx": abs(latest_cash.get("capitalExpenditure", 0)),
            "Buybacks": abs(latest_cash.get("commonStockRepurchased", 0)),
            "Dividends": abs(latest_cash.get("dividendPaid", 0)),
            "Debt Repayment": abs(latest_cash.get("debtRepayment", 0)),
            "Acquisitions": abs(latest_cash.get("acquisitionsNet", 0)),
        }

        alloc_labels = [k for k in alloc_latest.keys()]
        alloc_values = [v for v in alloc_latest.values()]

        fig_alloc = go.Figure(
            data=[go.Pie(labels=alloc_labels, values=alloc_values, hole=0.4)]
        )
        fig_alloc.update_layout(title="Capital Deployment Breakdown (Latest FY)")
        st.plotly_chart(fig_alloc, )

        st.write("---")

        # --------------------------------
        # Trends: CapEx / Buybacks / Dividends / Debt
        # --------------------------------
        st.subheader("Capital Deployment Trends")

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_alloc["date"], y=df_alloc["CapEx"], name="CapEx", mode="lines+markers"
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_alloc["date"], y=df_alloc["Buybacks"], name="Share Repurchases", mode="lines+markers"
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_alloc["date"], y=df_alloc["Dividends"], name="Dividends", mode="lines+markers"
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_alloc["date"], y=df_alloc["DebtRepay"], name="Debt Repayment", mode="lines+markers"
        ))

        fig_trend.update_layout(title="Capital Deployment Trends (Multi-Year)")
        st.plotly_chart(fig_trend)

        st.write("---")

        # --------------------------------
        # Capital Allocation Insights (Auto-Generated)
        # --------------------------------
        st.subheader("Capital Allocation Insights")

        insights = []

        # Insight 1: Buyback strategy
        # if abs(buybacks) > abs(dividends) * 2:
        #     insights.append("• Capital allocation is strongly weighted toward stock buybacks over dividends.")
        # elif abs(dividends) > abs(buybacks):
        #     insights.append("• Company emphasizes dividends over buybacks.")

        # Insight 2: Debt policy
        if abs(debt_repayment) > 0:
            insights.append("• Company continues to deleverage through debt repayments.")
        if total_debt == 0:
            insights.append("• Company operates with no meaningful debt — extremely conservative balance sheet.")

        # Insight 3: FCF allocation balance
        fcf = latest_cash.get("freeCashFlow", np.nan)
        # if not pd.isna(fcf) and fcf > 0:
        #     deployment_ratio = (
        #         abs(buybacks) + abs(dividends) + abs(latest_cash.get("capitalExpenditure", 0))
        #     ) / fcf
        #     if deployment_ratio > 1.2:
        #         insights.append("• Capital returns & reinvestment exceed FCF — company may be using cash reserves or debt.")
        #     elif deployment_ratio < 0.7:
        #         insights.append("• Company is retaining a significant portion of FCF rather than deploying it.")

        # Insight 4: Acquisitions
        acquisitions = latest_cash.get("acquisitionsNet", 0)
        if abs(acquisitions) > Decimal(1e9):  # > $1B
            insights.append("• Significant M&A activity detected in the latest year.")

        # Display insights
        if len(insights) == 0:
            st.info("No major capital allocation observations detected.")
        else:
            for i in insights:
                st.write(i)

        st.write("---")
