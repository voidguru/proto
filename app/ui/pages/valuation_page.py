"""
Valuation Page
"""
from decimal import Decimal
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from app.ui.base_page import BasePage


class ValuationPage(BasePage):
    def render(self):
        st.header("Valuation")

        # -------------------------
        # Load Data
        # -------------------------
        df_m = pd.DataFrame(self.state.metrics_df.sort_values("date"))
        df_fm = pd.DataFrame(self.state.financials_df.sort_values("date"))
        df_is = self.state.income_statement_df.sort_values("date")

        for df in (df_m, df_fm, df_is):
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])

        if df_m.empty:
            st.warning("No 'metrics' data available for valuation analysis.")
            return

        latest_m = df_m.iloc[-1]
        latest_fm = df_fm.iloc[-1] if not df_fm.empty else pd.Series()
        latest_is = df_is.iloc[-1]

        # -------------------------
        # TOP KPI PANEL
        # -------------------------
        st.subheader("Valuation Snapshot (Latest)")

        k1, k2, k3, k4 = st.columns(4)

        # Market Cap
        mc = latest_m.get("marketCap", np.nan)
        k1.metric("Market Cap", f"${mc/Decimal(1e9):,.2f}B" if not pd.isna(mc) else "n/a")

        # Enterprise Value
        ev = latest_m.get("enterpriseValue", latest_fm.get("enterpriseValue", np.nan))
        k2.metric("Enterprise Value", f"${ev/Decimal(1e9):,.2f}B" if not pd.isna(ev) else "n/a")

        # P/E Ratio
        pe = latest_m.get("priceToEarningsRatio", latest_fm.get("priceToEarningsRatio", np.nan))
        k3.metric("P/E Ratio", f"{pe:.2f}" if not pd.isna(pe) else "n/a")

        # EV/EBITDA
        ev_ebitda = latest_m.get("evToEBITDA", latest_fm.get("evToEBITDA", np.nan))
        k4.metric("EV/EBITDA", f"{ev_ebitda:.2f}" if not pd.isna(ev_ebitda) else "n/a")

        st.write("---")

        # -------------------------
        # Valuation Multiples Over Time
        # -------------------------
        st.subheader("Valuation Multiples — Multi-Year Trend")

        multiple_map = {
            "P/E Ratio": "priceToEarningsRatio",
            "P/S Ratio": "priceToSalesRatio",
            "P/B Ratio": "priceToBookRatio",
            "EV/EBITDA": "evToEBITDA",
            "EV/OpCF": "evToOperatingCashFlowRatio",
            "EV/FreeCashFlow": "enterpriseValueOverEBITDA", 
        }

        fig_mult = go.Figure()

        for label, col in multiple_map.items():
            if col in df_m.columns:
                s = df_m[["date", col]].dropna()
            elif col in df_fm.columns:
                s = df_fm[["date", col]].dropna()
            else:
                continue

            if not s.empty:
                fig_mult.add_trace(go.Scatter(
                    x=s["date"],
                    y=s[col],
                    mode="lines+markers",
                    name=label
                ))

        fig_mult.update_layout(
            title="Valuation Multiples Over Time",
            yaxis_title="Multiple"
        )
        st.plotly_chart(fig_mult, )

        st.write("---")

        # -------------------------
        # EV vs Market Cap Over Time
        # -------------------------
        st.subheader("Enterprise Value vs Market Cap")

        df_val = df_m.copy()
        if not df_fm.empty:
            for col in ["enterpriseValue", "marketCap"]:
                if col not in df_val.columns and col in df_fm.columns:
                    df_val[col] = df_fm[col]

        if "marketCap" in df_val.columns and "enterpriseValue" in df_val.columns:
            fig_ev = go.Figure()
            fig_ev.add_trace(go.Line(x=df_val["date"], y=df_val["marketCap"], name="Market Cap"))
            fig_ev.add_trace(go.Line(x=df_val["date"], y=df_val["enterpriseValue"], name="Enterprise Value"))
            fig_ev.update_layout(
                title="EV vs Market Cap Over Time",
                yaxis_title="USD"
            )
            st.plotly_chart(fig_ev, )
        else:
            st.info("Missing EV or Market Cap fields.")

        st.write("---")

        # -------------------------
        # Earnings Yield & FCF Yield
        # -------------------------
        st.subheader("Earnings & Cash Flow Yields")

        df_yield = df_m.copy()

        # Earnings Yield = 1 / PE
        df_yield["earnings_yield"] = np.where(
            df_fm.get("priceToEarningsRatio", np.nan) > 0,
            1 / df_fm.get("priceToEarningsRatio", np.nan),
            np.nan
        )

        # FCF yield = freeCashFlowPerShare / price
        if "freeCashFlowPerShare" in df_fm.columns and "price" in df_fm.columns:
            df_yield["fcf_yield"] = df_fm["freeCashFlowPerShare"] / df_fm["price"]
        else:
            df_yield["fcf_yield"] = np.nan

        fig_yield = go.Figure()
        fig_yield.add_trace(go.Line(
            x=df_yield["date"], y=df_yield["earnings_yield"], name="Earnings Yield"
        ))
        fig_yield.add_trace(go.Line(
            x=df_yield["date"], y=df_yield["fcf_yield"], name="FCF Yield"
        ))
        fig_yield.update_layout(title="Earnings & FCF Yields", yaxis_title="Yield")
        st.plotly_chart(fig_yield, )

        st.write("---")

        # -------------------------
        # Historical Multiple Bands (Regression-based)
        # -------------------------
        st.subheader("Regression Valuation Bands (P/E Based)")

        if "priceToEarningsRatio" in df_yield.columns:
            valid = df_yield[['date', 'priceToEarningsRatio', 'price']].dropna()
            if len(valid) > 5:
                # Estimate price implied by historical average multiple
                avg_pe = valid["priceToEarningsRatio"].mean()
                latest_eps = latest_is.get("eps", np.nan)

                if not pd.isna(latest_eps):
                    implied_price = avg_pe * latest_eps

                    st.metric(
                        "Price Implied by Historical P/E",
                        f"${implied_price:,.2f}"
                    )

                    # Plot actual price vs implied band
                    df_yield["implied_price"] = df_yield["priceToEarningsRatio"].mean() * df_is.get("eps", np.nan)
                    fig_band = go.Figure()
                    fig_band.add_trace(go.Line(x=df_yield["date"], y=df_yield["price"], name="Actual Price"))
                    fig_band.add_trace(go.Line(x=df_yield["date"], y=df_yield["implied_price"], name="Implied Price (Avg P/E)"))
                    fig_band.update_layout(title="Valuation Band: Price vs Implied Value")
                    st.plotly_chart(fig_band, )
                else:
                    st.info("No EPS available for implied valuation.")
            else:
                st.info("Not enough historical data for regression valuation bands.")
        else:
            st.info("Need P/E and price fields to compute valuation bands.")

        st.write("---")

        # -------------------------
        # Valuation Scorecard (Simple Rules)
        # -------------------------
        st.subheader("Valuation Scorecard")

        score = 0
        max_score = 500

        # P/E
        if not pd.isna(pe):
            if pe < 15:
                score += 90
            elif pe < 25:
                score += 70
            elif pe < 35:
                score += 50
            else:
                score += 20
        else:
            score += 50

        # EV/EBITDA
        if not pd.isna(ev_ebitda):
            if ev_ebitda < 10:
                score += 90
            elif ev_ebitda < 16:
                score += 70
            elif ev_ebitda < 22:
                score += 50
            else:
                score += 20
        else:
            score += 50

        # Price-to-Sales
        ps = latest_m.get("priceToSalesRatio", np.nan)
        if not pd.isna(ps):
            if ps < 3:
                score += 90
            elif ps < 6:
                score += 70
            elif ps < 10:
                score += 50
            else:
                score += 20
        else:
            score += 50

        # Price-to-Book
        pb = latest_m.get("priceToBookRatio", np.nan)
        if not pd.isna(pb):
            if pb < 3:
                score += 90
            elif pb < 6:
                score += 70
            else:
                score += 40
        else:
            score += 50

        # FCF Yield
        fcf_y = df_yield["fcf_yield"].iloc[-1]
        if not pd.isna(fcf_y):
            if fcf_y > 0.06:
                score += 90
            elif fcf_y > 0.04:
                score += 7
