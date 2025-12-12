"""
Financial Strength Page
"""
from decimal import Decimal
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.ui.base_page import BasePage

class FinancialStrengthPage(BasePage):
    def render(self):
        st.header("Financial Strength — Quantitative Diagnostics")

        # -------------------------
        # Load & prepare data
        # -------------------------
        # self.data is assumed to be a dict of DataFrames or lists
        df_bs = self.state.balance_sheet_df.sort_values("date")
        df_cf = self.state.cashflow_df.sort_values("date")
        df_metrics = self.state.metrics_df.sort_values("date")
        df_fin = self.state.financials_df.sort_values("date")

        # Ensure date columns are datetime where present
        for df in (df_bs, df_cf, df_metrics, df_fin):
            if df is None or df.empty:
                continue
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])

        # pick latest safe rows
        latest_bs = df_bs.iloc[-1] if not df_bs.empty else pd.Series()
        latest_cf = df_cf.iloc[-1] if not df_cf.empty else pd.Series()
        latest_metrics = df_metrics.iloc[-1] if not df_metrics.empty else pd.Series()
        latest_fin = df_fin.iloc[-1] if not df_fin.empty else pd.Series()

        # -------------------------
        # KPI BAR (Top)
        # -------------------------
        st.subheader("Top Liquidity & Solvency KPIs")

        k1, k2, k3, k4, k5 = st.columns(5)

        # Cash & short-term investments (balance sheet)
        cash_and_st = (
            latest_bs.get("cashAndShortTermInvestments")
            or (latest_bs.get("cashAndCashEquivalents") + latest_bs.get("shortTermInvestments", 0))
            or np.nan
        )
        k1.metric("Cash + Short-term Inv.", f"${(cash_and_st or np.nan)/Decimal(1e9):,.2f}B")

        # Total debt & net debt
        total_debt = latest_bs.get("totalDebt", latest_bs.get("longTermDebt", 0) + latest_bs.get("shortTermDebt", 0))
        net_debt = latest_bs.get("netDebt", latest_bs.get("totalDebt", np.nan) - cash_and_st) if not pd.isna(latest_bs.get("netDebt", np.nan)) else np.nan
        k2.metric("Total Debt", f"${(total_debt or np.nan)/Decimal(1e9):,.2f}B")
        k3.metric("Net Debt", f"${(net_debt or np.nan)/Decimal(1e9):,.2f}B")

        # Net debt / EBITDA (from metrics or compute)
        nd_to_ebitda = latest_metrics.get("netDebtToEBITDA", np.nan)
        if pd.isna(nd_to_ebitda):
            # attempt compute
            ebitda = latest_bs.get("ebitda", latest_cf.get("ebitda", np.nan)) if not pd.isna(latest_bs.get("ebitda", np.nan)) else latest_metrics.get("ebitda")
            if (not pd.isna(net_debt)) and (not pd.isna(ebitda)) and ebitda != 0:
                nd_to_ebitda = net_debt / ebitda
        k4.metric("Net Debt / EBITDA", f"{nd_to_ebitda:.2f}x" if not pd.isna(nd_to_ebitda) else "n/a")

        # Current ratio (prefers metrics)
        current_ratio = latest_metrics.get("currentRatio", latest_bs.get("totalCurrentAssets") / latest_bs.get("totalCurrentLiabilities") if (not df_bs.empty and latest_bs.get("totalCurrentLiabilities", 0) != 0) else np.nan)
        k5.metric("Current Ratio", f"{current_ratio:.2f}" if not pd.isna(current_ratio) else "n/a")

        st.write("---")

        # -------------------------
        # Liquidity Ratios Trend
        # -------------------------
        st.subheader("Liquidity Ratios — Multi-year Trend")

        liquidity_cols = []
        if not df_metrics.empty and "currentRatio" in df_metrics.columns:
            liquidity_cols.append(("Current Ratio", "currentRatio"))
        if not df_metrics.empty and "quickRatio" in df_metrics.columns:
            liquidity_cols.append(("Quick Ratio", "quickRatio"))
        if not df_metrics.empty and "cashRatio" in df_metrics.columns:
            liquidity_cols.append(("Cash Ratio", "cashRatio"))

        if liquidity_cols:
            fig = go.Figure()
            for label, col in liquidity_cols:
                series = df_metrics[[ "date", col ]].dropna()
                if not series.empty:
                    fig.add_trace(go.Line(x=series["date"], y=series[col], name=label))
            fig.update_layout(title="Liquidity Ratios Over Time", yaxis_title="Ratio")
            st.plotly_chart(fig, )
        else:
            st.info("No multi-year liquidity ratios available in metrics table.")

        # -------------------------
        # Leverage & Debt Composition
        # -------------------------
        st.subheader("Leverage & Debt Composition")

        # Debt composition chart: short-term vs long-term debt (balance sheet)
        debt_components = []
        if not df_bs.empty:
            for col, name in [("shortTermDebt", "Short-Term Debt"), ("longTermDebt", "Long-Term Debt")]:
                if col in df_bs.columns:
                    debt_components.append((name, col))
        if debt_components:
            fig_debt = go.Figure()
            for name, col in debt_components:
                fig_debt.add_trace(go.Bar(x=df_bs["date"], y=df_bs[col], name=name))
            # plot cash on top as negative (to show net-debt visually)
            if "cashAndShortTermInvestments" in df_bs.columns:
                fig_debt.add_trace(go.Bar(x=df_bs["date"], y=-df_bs["cashAndShortTermInvestments"], name="Cash & ST Inv. (offset)"))
            fig_debt.update_layout(barmode="stack", title="Debt Composition vs Cash (stacked)")
            st.plotly_chart(fig_debt, )
        else:
            st.info("No short/long-term debt fields present to chart composition.")

        # Leverage ratios trend (debtToEquity, debtToAssets, financialLeverage)
        leverage_cols = []
        for col in ["debtToEquityRatio", "debtToAssetsRatio", "financialLeverageRatio", "debtToCapitalRatio"]:
            if col in df_fin.columns:
                leverage_cols.append(col)

        if leverage_cols:
            fig_lev = go.Figure()
            for col in leverage_cols:
                fig_lev.add_trace(go.Line(x=df_fin["date"], y=df_fin[col], name=col))
            fig_lev.update_layout(title="Leverage Ratios Over Time", yaxis_title="Ratio")
            st.plotly_chart(fig_lev, )

        st.write("---")

        # -------------------------
        # Coverage & Capacity to Service Debt
        # -------------------------
        st.subheader("Coverage Ratios & Interest Burden")

        coverage_series = []
        if "interestCoverageRatio" in df_fin.columns:
            coverage_series.append(("Interest Coverage (reported)", "interestCoverageRatio"))
        if "debtServiceCoverageRatio" in df_fin.columns:
            coverage_series.append(("Debt Service Coverage", "debtServiceCoverageRatio"))
        if "operatingCashFlowCoverageRatio" in df_fin.columns:
            coverage_series.append(("OpCF Coverage Ratio", "operatingCashFlowCoverageRatio"))
        if coverage_series:
            fig_cov = go.Figure()
            for label, col in coverage_series:
                s = df_fin[["date", col]].dropna()
                if not s.empty:
                    fig_cov.add_trace(go.Line(x=s["date"], y=s[col], name=label))
            fig_cov.update_layout(title="Coverage Ratios Over Time", yaxis_title="Ratio")
            st.plotly_chart(fig_cov, )
        else:
            st.info("No coverage ratios in financial metrics to chart.")

        # Interest paid vs EBIT (compute interest coverage if not present)
        if ("interestPaid" in df_cf.columns) and (("ebit" in df_cf.columns) or ("ebit" in df_fin.columns) or ("ebit" in df_cf.columns)):
            # try to align series from cashflow and income
            ebit_series = None
            income_df = self.state.get("income_statement", []).sort_values("date")
            if not income_df.empty and "ebit" in income_df.columns:
                ebit_series = income_df[["date", "ebit"]]
            elif "ebit" in df_cf.columns:
                ebit_series = df_cf[["date", "ebit"]]
            interest_series = df_cf[["date", "interestPaid"]].dropna()
            if ebit_series is not None and not interest_series.empty:
                merged = pd.merge(ebit_series, interest_series, on="date", how="inner").dropna()
                if not merged.empty:
                    merged["interest_coverage"] = merged["ebit"] / merged["interestPaid"].replace({0: np.nan})
                    fig_ic = px.line(merged, x="date", y="interest_coverage", title="Computed Interest Coverage (EBIT / Interest Paid)", markers=True)
                    st.plotly_chart(fig_ic, )

        st.write("---")

        # -------------------------
        # Working Capital & Cash Conversion
        # -------------------------
        st.subheader("Working Capital Components & Cash Conversion")

        # Build components if present in balance sheet or cashflow
        wc_df = None
        # prefer balance sheet components over cashflow line items
        if not df_bs.empty and set(["accountsReceivables", "inventory", "totalPayables"]).issubset(set(df_bs.columns)):
            wc_df = df_bs[["date", "accountsReceivables", "inventory", "totalPayables"]].copy()
            wc_df = wc_df.rename(columns={"accountsReceivables": "Receivables", "inventory": "Inventory", "totalPayables": "Payables"})
        elif not df_cf.empty and set(["accountsReceivables", "inventory", "accountsPayables"]).issubset(set(df_cf.columns)):
            wc_df = df_cf[["date", "accountsReceivables", "inventory", "accountsPayables"]].copy()
            wc_df = wc_df.rename(columns={"accountsReceivables": "Receivables", "inventory": "Inventory", "accountsPayables": "Payables"})
        if wc_df is not None:
            fig_wc = go.Figure()
            fig_wc.add_trace(go.Bar(x=wc_df["date"], y=wc_df["Receivables"], name="Receivables"))
            fig_wc.add_trace(go.Bar(x=wc_df["date"], y=wc_df["Inventory"], name="Inventory"))
            fig_wc.add_trace(go.Bar(x=wc_df["date"], y=wc_df["Payables"], name="Payables"))
            fig_wc.update_layout(barmode="group", title="Working Capital Components")
            st.plotly_chart(fig_wc, )
        else:
            st.info("No detailed working capital components available to chart.")

        # Cash conversion cycle (metrics)
        if "cashConversionCycle" in df_metrics.columns:
            ccc = df_metrics[["date", "cashConversionCycle"]].dropna()
            fig_ccc = px.line(ccc, x="date", y="cashConversionCycle", title="Cash Conversion Cycle (days)", markers=True)
            st.plotly_chart(fig_ccc, )
            st.write(f"Latest CCC: {ccc['cashConversionCycle'].iloc[-1]:.1f} days")
        else:
            st.info("cashConversionCycle not present in metrics.")

        st.write("---")

        # -------------------------
        # Net Debt / Liquidity Waterfall
        # -------------------------
        st.subheader("Net Debt vs Liquidity & Short-Term Investments")

        if not df_bs.empty:
            df_nd = df_bs.copy()
            # compute cash-like = cashAndShortTermInvestments (fallback)
            if "cashAndShortTermInvestments" in df_nd.columns:
                df_nd["cash_like"] = df_nd["cashAndShortTermInvestments"]
            else:
                df_nd["cash_like"] = df_nd.get("cashAndCashEquivalents", 0) + df_nd.get("shortTermInvestments", 0)
            df_nd["net_debt_calc"] = df_nd.get("totalDebt", 0) - df_nd["cash_like"]
            fig_nd = go.Figure()
            fig_nd.add_trace(go.Bar(x=df_nd["date"], y=df_nd["totalDebt"], name="Total Debt"))
            fig_nd.add_trace(go.Bar(x=df_nd["date"], y=df_nd["cash_like"], name="Cash & ST Inv."))
            fig_nd.add_trace(go.Line(x=df_nd["date"], y=df_nd["net_debt_calc"], name="Net Debt (calc)", yaxis="y2"))
            # add second y-axis
            fig_nd.update_layout(
                title="Total Debt vs Cash-like Assets (Net Debt overlay)",
                yaxis_title="USD",
                yaxis2=dict(title="Net Debt", overlaying="y", side="right")
            )
            st.plotly_chart(fig_nd, )
        else:
            st.info("Balance sheet needed for net debt chart.")

        st.write("---")

        # -------------------------
        # Solvency Radar (normalized metrics)
        # -------------------------
        st.subheader("Solvency Radar — relative view")

        radar_items = []
        radar_cols = {
            "Current Ratio": "currentRatio",
            "Quick Ratio": "quickRatio",
            "Cash Ratio": "cashRatio",
            "Debt/Equity": "debtToEquityRatio",
            "NetDebt/EBITDA": "netDebtToEBITDA",
            "Interest Coverage": "interestCoverageRatio",
            "OpCF Coverage": "operatingCashFlowCoverageRatio"
        }
        latest_vals = {}
        for label, col in radar_cols.items():
            val = None
            if col in latest_metrics:
                val = latest_metrics.get(col)
            elif col in latest_fin:
                val = latest_fin.get(col)
            else:
                val = np.nan
            # coerce netDebtToEBITDA naming
            if col == "netDebtToEBITDA" and pd.isna(val):
                val = latest_metrics.get("netDebtToEBITDA", np.nan)
            latest_vals[label] = val

        # If at least 3 metrics available, plot radar
        available = {k: v for k, v in latest_vals.items() if (not pd.isna(v))}
        if len(available) >= 3:
            # normalize each metric for radar plotting (simple percentile-style scaling)
            labels = list(available.keys())
            values = np.array([abs(available[l]) for l in labels], dtype=float)
            # scale to 0-1 by dividing by a robust scale (median*3 or 1 if zero)
            scale = np.median(values) * 3 if np.median(values) > 0 else 1.0
            values_scaled = (values / scale).clip(0, 1)
            # close the loop
            labels_loop = labels + [labels[0]]
            vals_loop = list(values_scaled) + [values_scaled[0]]
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=vals_loop, theta=labels_loop, fill='toself', name="Latest (normalized)"))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])), showlegend=False, title="Solvency Radar (normalized)")
            st.plotly_chart(fig_radar, )
        else:
            st.info("Not enough solvency metrics available for radar (need >=3).")

        st.write("---")

        # -------------------------
        # Quantitative Risk Scorecard
        # -------------------------
        st.subheader("Quantitative Risk Scorecard (simple rule-based)")

        # Score components (0..100 each)
        score = 0
        max_score = 500  # 5 categories * 100

        # Liquidity score (current ratio)
        lr = current_ratio if not pd.isna(current_ratio) else None
        if lr is None:
            liq_score = 50
        else:
            if lr >= 1.5:
                liq_score = 90
            elif lr >= 1.0:
                liq_score = 70
            elif lr >= 0.8:
                liq_score = 50
            else:
                liq_score = 20
        score += liq_score

        # Leverage score (netDebt/EBITDA)
        nd_score = 50
        if not pd.isna(nd_to_ebitda):
            if nd_to_ebitda < 1:
                nd_score = 90
            elif nd_to_ebitda < 2:
                nd_score = 70
            elif nd_to_ebitda < 3:
                nd_score = 50
            else:
                nd_score = 20
        score += nd_score

        # Coverage score (interest coverage)
        ic = latest_fin.get("interestCoverageRatio", np.nan)
        if pd.isna(ic) and "interestPaid" in latest_cf and "ebit" in latest_cf:
            ic = (latest_cf.get("ebit") / (latest_cf.get("interestPaid") or np.nan)) if latest_cf.get("interestPaid", 0) != 0 else np.nan
        if pd.isna(ic):
            ic_score = 50
        else:
            if ic >= 10:
                ic_score = 90
            elif ic >= 4:
                ic_score = 70
            elif ic >= 2:
                ic_score = 50
            else:
                ic_score = 20
        score += ic_score

        # Cash generation score (operating cash flow / debt)
        ocf = latest_cf.get("operatingCashFlow", latest_metrics.get("operatingCashFlow", np.nan))
        if (not pd.isna(ocf)) and (not pd.isna(total_debt)) and total_debt != 0:
            ocf_debt = ocf / total_debt
            if ocf_debt > 0.5:
                ocf_score = 90
            elif ocf_debt > 0.2:
                ocf_score = 70
            elif ocf_debt > 0.1:
                ocf_score = 50
            else:
                ocf_score = 30
        else:
            ocf_score = 50
        score += ocf_score

        # Working capital health (cash conversion cycle)
        ccc_val = latest_metrics.get("cashConversionCycle", np.nan)
        if pd.isna(ccc_val):
            ccc_score = 50
        else:
            # shorter (especially negative) is better
            if ccc_val < 0:
                ccc_score = 90
            elif ccc_val < 30:
                ccc_score = 70
            elif ccc_val < 60:
                ccc_score = 50
            else:
                ccc_score = 20
        score += ccc_score

        # Display scorecard
        st.markdown(f"**Aggregate Risk Score:** **{int(score / max_score * 100)} / 100**")
        st.write(f"- Liquidity score: {liq_score} / 100")
        st.write(f"- Leverage score: {nd_score} / 100")
        st.write(f"- Coverage score: {ic_score} / 100")
        st.write(f"- Cash generation score: {ocf_score} / 100")
        st.write(f"- Working capital score: {ccc_score} / 100")

        st.write("---")
        st.markdown("**Notes & sources:** This page uses balance-sheet, cashflow and pre-computed metrics fields from your uploaded dataset (e.g. `cashAndShortTermInvestments`, `totalDebt`, `netDebt`, liquidity & leverage ratios in `metrics` and `financial_metrics`, `operatingCashFlow`, `ebitda`, `interestPaid`, and `cashConversionCycle`). See mock_data.json for field examples. :contentReference[oaicite:3]{index=3} :contentReference[oaicite:4]{index=4} :contentReference[oaicite:5]{index=5}")
