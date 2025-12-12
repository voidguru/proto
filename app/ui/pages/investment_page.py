"""
Investment Page
"""
from decimal import Decimal
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.ui.base_page import BasePage

class InvestmentPage(BasePage):

    def render(self):
        st.header("Investment")

        # ---------------------------
        # Load & prepare data
        # ---------------------------
        df_cash = self.state.cashflow_df.sort_values("date")
        df_bs = self.state.balance_sheet_df.sort_values("date")
        df_income = self.state.income_statement_df.sort_values("date")
        df_metrics = self.state.metrics_df.sort_values("date")
        df_finmetrics = self.state.financials_df.sort_values("date")

        # Ensure date is treated consistently
        for df in (df_cash, df_bs, df_income, df_metrics, df_finmetrics):
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])

        if df_cash.empty:
            st.warning("No cash flow data available for Investment analysis.")
            return

        # Latest rows (safe access)
        latest_cash = df_cash.iloc[-1] if not df_cash.empty else pd.Series()
        latest_income = df_income.iloc[-1] if not df_income.empty else pd.Series()
        latest_bs = df_bs.iloc[-1] if not df_bs.empty else pd.Series()
        latest_metrics = df_metrics.iloc[-1] if not df_metrics.empty else pd.Series()
        latest_finmetrics = df_finmetrics.iloc[-1] if not df_finmetrics.empty else pd.Series()

        # ---------------------------
        # Top KPI row: Investment-centric KPIs
        # ---------------------------
        st.subheader("Investment KPIs")
        k1, k2, k3, k4 = st.columns(4)

        # Capex (abs value)
        capex = latest_cash.get("capitalExpenditure", np.nan)
        k1.metric(
            "CapEx (Latest FY)",
            f"${abs(capex) / Decimal(1e9):,.2f}B" if not pd.isna(capex) else "n/a"
        )

        # Invested Capital (prefer metrics.investedCapital)
        invested_capital = latest_metrics.get("investedCapital", np.nan)
        if pd.isna(invested_capital) and not df_bs.empty:
            # fallback: totalAssets - cash & short-term investments
            invested_capital = latest_bs.get("totalAssets", np.nan) - latest_bs.get("cashAndShortTermInvestments", latest_bs.get("cashAndCashEquivalents", 0))
        k2.metric(
            "Invested Capital",
            f"${invested_capital / Decimal(1e9):,.2f}B" if not pd.isna(invested_capital) else "n/a"
        )

        # ROIC (prefer metrics.returnOnInvestedCapital)
        roic = latest_metrics.get("returnOnInvestedCapital", latest_finmetrics.get("returnOnInvestedCapital", np.nan))
        k3.metric("ROIC (Latest)", f"{roic * 100:.2f}%" if not pd.isna(roic) else "n/a")

        # FCF to Firm (use metrics.freeCashFlowToFirm if present else use freeCashFlow)
        fcf_to_firm = latest_metrics.get("freeCashFlowToFirm", latest_cash.get("freeCashFlow", np.nan))
        k4.metric(
            "Free Cash Flow (Firm, Latest)",
            f"${fcf_to_firm / Decimal(1e9):,.2f}B" if not pd.isna(fcf_to_firm) else "n/a"
        )

        st.write("---")

        # ---------------------------
        # Capex & Investments Trend
        # ---------------------------
        st.subheader("CapEx & Investment Activity")

        # Create a dataframe for capex and investment flows
        df_inv = df_cash.copy()

        # Normalize column names / fallbacks for investment-related fields
        # purchasesOfInvestments / purchasesOfInvestments is present in mock
        # salesMaturitiesOfInvestments present as salesMaturitiesOfInvestments
        df_inv["purchasesOfInvestments"] = df_inv.get("purchasesOfInvestments", df_inv.get("purchaseOfInvestment", 0)).fillna(0)
        df_inv["salesMaturitiesOfInvestments"] = df_inv.get("salesMaturitiesOfInvestments", df_inv.get("saleOfInvestment", 0)).fillna(0)
        df_inv["acquisitionsNet"] = df_inv.get("acquisitionsNet", 0).fillna(0)

        # Plot CapEx, Purchases & Sales of Investments, Acquisitions
        fig_inv = go.Figure()
        if "capitalExpenditure" in df_inv.columns:
            fig_inv.add_trace(go.Bar(x=df_inv["date"], y=df_inv["capitalExpenditure"], name="CapEx"))
        if "purchasesOfInvestments" in df_inv.columns:
            fig_inv.add_trace(go.Bar(x=df_inv["date"], y=df_inv["purchasesOfInvestments"], name="Purchases of Investments"))
        if "salesMaturitiesOfInvestments" in df_inv.columns:
            fig_inv.add_trace(go.Bar(x=df_inv["date"], y=df_inv["salesMaturitiesOfInvestments"], name="Sales / Maturities of Investments"))
        # acquisitions (M&A) often negative (cash out)
        if "acquisitionsNet" in df_inv.columns:
            fig_inv.add_trace(go.Bar(x=df_inv["date"], y=df_inv["acquisitionsNet"], name="Acquisitions (Net)"))

        fig_inv.update_layout(barmode="group", title="CapEx & Investment Activity (cash basis)")
        st.plotly_chart(fig_inv)

        st.write("---")

        # ---------------------------
        # ROIC & Returns Trend
        # ---------------------------
        st.subheader("Returns on Capital")

        # Build ROIC time series: prefer df_metrics.returnOnInvestedCapital, otherwise compute
        if "returnOnInvestedCapital" in df_metrics.columns:
            df_roic = df_metrics[["date", "returnOnInvestedCapital"]].copy()
            df_roic = df_roic.dropna(subset=["returnOnInvestedCapital"])
            df_roic["roic_pct"] = df_roic["returnOnInvestedCapital"] * 100
            fig_roic = px.line(df_roic, x="date", y="roic_pct", title="ROIC (%)", markers=True)
            st.plotly_chart(fig_roic)
        else:
            # Attempt to compute ROIC = NOPAT / InvestedCapital
            if "ebit" in df_income.columns:
                df_roic_calc = df_income[["date", "ebit"]].copy()
                # Use effectiveTaxRate from financial_metrics if available, else metrics.effectiveTaxRate or 25% fallback
                tax_rate_series = df_finmetrics.get("effectiveTaxRate", df_finmetrics.get("effectiveTaxRate", None))
                if tax_rate_series is None or tax_rate_series.isna().all():
                    tax_rate = 0.25
                else:
                    # align by date if possible
                    tax_rate = float(df_finmetrics.iloc[-1].get("effectiveTaxRate", 0.25))
                df_roic_calc["nopat"] = df_roic_calc["ebit"] * (1 - tax_rate)
                # invested capital series from metrics if available else approximate from balance sheet
                invested_series = df_metrics.get("investedCapital")
                if invested_series is not None:
                    df_roic_calc["investedCapital"] = invested_series.values
                elif "totalAssets" in df_bs.columns:
                    df_roic_calc["investedCapital"] = df_bs["totalAssets"].values - df_bs.get("cashAndShortTermInvestments", df_bs.get("cashAndCashEquivalents", 0)).values
                else:
                    df_roic_calc["investedCapital"] = np.nan
                df_roic_calc["roic"] = df_roic_calc["nopat"] / df_roic_calc["investedCapital"]
                df_roic_calc = df_roic_calc.dropna(subset=["roic"])
                df_roic_calc["roic_pct"] = df_roic_calc["roic"] * 100
                fig_roic = px.line(df_roic_calc, x="date", y="roic_pct", title="Computed ROIC (%)", markers=True)
                st.plotly_chart(fig_roic)
            else:
                st.info("ROIC data not available and insufficient fields to compute ROIC.")

        st.write("---")

        # ---------------------------
        # Investment Efficiency & Ratios
        # ---------------------------
        st.subheader("Investment Efficiency")

        col1, col2, col3 = st.columns(3)

        # Capex to Sales
        if "revenue" in df_income.columns and "capitalExpenditure" in df_cash.columns:
            latest_revenue = latest_income.get("revenue", np.nan)
            capex_to_revenue = abs(capex) / latest_revenue
            col1.metric("CapEx / Revenue (Latest)", f"{capex_to_revenue * 100:.2f}%" if not pd.isna(capex_to_revenue) else "n/a")
        else:
            col1.metric("CapEx / Revenue (Latest)", "n/a")

        # Capex / Depreciation
        if "depreciationAndAmortization" in df_cash.columns:
            depr = latest_cash.get("depreciationAndAmortization", np.nan)
            capex_to_depr = abs(capex) / depr if (not pd.isna(capex) and not pd.isna(depr) and depr != 0) else np.nan
            col2.metric("CapEx / Depreciation (Latest)", f"{capex_to_depr:.2f}x" if not pd.isna(capex_to_depr) else "n/a")
        else:
            col2.metric("CapEx / Depreciation (Latest)", "n/a")

        # Return on Invested Capital (alternative display)
        if not pd.isna(roic):
            col3.metric("ROIC (display)", f"{roic * 100:.2f}%")
        else:
            col3.metric("ROIC (display)", "n/a")

        st.write("---")

        # ---------------------------
        # Acquisition & Investment Notes
        # ---------------------------
        st.subheader("Acquisitions & Investment Deployment")

        # Summarize acquisition cash flows and purchases/sales of investments
        acq_series = df_cash.get("acquisitionsNet", pd.Series(dtype=float)).fillna(0)
        purchases = df_cash.get("purchasesOfInvestments", df_cash.get("purchasesOfInvestments", pd.Series(dtype=float))).fillna(0)
        sales = df_cash.get("salesMaturitiesOfInvestments", df_cash.get("salesMaturitiesOfInvestments", pd.Series(dtype=float))).fillna(0)

        # Show aggregated recent activity
        if len(df_cash) > 0:
            total_acq = acq_series.sum() if not acq_series.empty else 0.0
            total_purchases = purchases.sum() if not purchases.empty else 0.0
            total_sales = sales.sum() if not sales.empty else 0.0

            st.write(f"- Total acquisitions (cash) over period: ${total_acq / Decimal(1e9):,.2f}B")
            st.write(f"- Total purchases of investments over period: ${total_purchases / Decimal(1e9):,.2f}B")
            st.write(f"- Total sales / maturities of investments over period: ${total_sales / Decimal(1e9):,.2f}B")
        else:
            st.info("No investing activity data available.")

        # Show a small chart for acquisitions and purchases/sales
        fig_acq = go.Figure()
        if not acq_series.empty:
            fig_acq.add_trace(go.Bar(x=df_cash["date"], y=acq_series, name="Acquisitions (Net)"))
        if not purchases.empty:
            fig_acq.add_trace(go.Bar(x=df_cash["date"], y=purchases, name="Purchases of Investments"))
        if not sales.empty:
            fig_acq.add_trace(go.Bar(x=df_cash["date"], y=sales, name="Sales / Maturities of Investments"))
        if len(fig_acq.data) > 0:
            fig_acq.update_layout(barmode="group", title="Acquisitions & Portfolio Investment Activity (cash)")
            st.plotly_chart(fig_acq)

        st.write("---")

        # ---------------------------
        # Investment Insights (auto-generated)
        # ---------------------------
        st.subheader("Investment Insights")

        insights = []

        # Insight: Capex behavior vs prior year
        if len(df_inv) >= 2:
            if df_inv["capitalExpenditure"].iloc[-1] < df_inv["capitalExpenditure"].iloc[-2]:
                insights.append("• CapEx decreased in the latest year versus prior year — potentially lower reinvestment needs or temporary pause.")
            else:
                insights.append("• CapEx increased in the latest year — management is investing more into the business.")

        # Insight: Investments net purchases vs sales
        net_portfolio_flow = df_inv["purchasesOfInvestments"].sum() + df_inv["acquisitionsNet"].sum() + df_inv["capitalExpenditure"].sum() + (- df_inv["salesMaturitiesOfInvestments"].sum() if "salesMaturitiesOfInvestments" in df_inv.columns else 0)
        if net_portfolio_flow is None:
            pass
        else:
            if net_portfolio_flow < 0:
                insights.append("• Net deployment of cash into investments/acquisitions over the period.")
            else:
                insights.append("• Net divestment / portfolio sales over the period.")

        # Insight: ROIC vs Capex intensity
        # if (not pd.isna(roic)) and (not pd.isna(capex_to_revenue if 'capex_to_revenue' in locals() else np.nan)):
        try:

            if capex_to_revenue < 0.03 and roic > 0.10:
                insights.append("• High ROIC with modest capex intensity — attractive capital-light returns profile.")
            elif capex_to_revenue > 0.05 and roic < 0.05:
                insights.append("• High reinvestment with low returns — monitor investment efficiency.")
        except Exception:
            st.write("DP")

        # Insight: Acquisition size
        if not acq_series.empty and acq_series.abs().max() > Decimal(1e9):
            insights.append("• Material acquisition activity detected — investigate strategic rationale and purchase price levels.")

        if len(insights) == 0:
            st.info("No automatic investment insights detected.")
        else:
            for i in insights:
                st.write(i)

        st.write("---")

        # ---------------------------
        # Download / Export Section (optional small widget)
        # ---------------------------
        st.subheader("Export Data")
        if st.button("Download investment activity CSV"):
            # compile a compact table
            export_cols = ["date"]
            for c in ["capitalExpenditure", "acquisitionsNet", "purchasesOfInvestments", "salesMaturitiesOfInvestments", "freeCashFlow"]:
                if c in df_cash.columns and c not in export_cols:
                    export_cols.append(c)
            export_df = df_cash[export_cols].copy()
            # Convert dates to iso
            export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d")
            csv = export_df.to_csv(index=False)
            st.download_button("Download CSV", data=csv, file_name="investment_activity.csv", mime="text/csv")
