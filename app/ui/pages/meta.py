"""
Valuation Playground Page (Modular FCF, 1-10 years, docs + charts)
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from app.ui.base_page import BasePage


class ValuationProblemsPage(BasePage):
    """
    Interactive valuation playground:
      - Modular DCF: choose horizon 1..10 and enter FCF values for each year
      - Choose terminal method: Perpetuity (g) or Terminal Multiple
      - Scenario presets (Conservative / Base / Optimistic)
      - Graphical projections: FCF line & bar + PV waterfall
      - Sensitivity table (small)
      - Inline documentation and link to the uploaded dataset
    """

    def render(self):
        st.title("Valuation Playground — Modular DCF & Dividend Models")
        st.markdown(
            """
            **Purpose:** Experiment with valuation assumptions and instantly see the impact on Enterprise Value,
            Equity Value, and Per-share implied value.

            **What you can do on this page**
            - Configure projection horizon (1 to 10 years) and input **modular FCF** for each year.
            - Choose discount rate (WACC), terminal approach (perpetuity with g or terminal multiple), and terminal parameters.
            - Apply scenario presets (Conservative / Base / Optimistic) and observe how projections, PV, and valuations change.
            - Visualize projected FCF (line + bar) and a **discounted PV waterfall** showing the contribution of each year's PV and the terminal PV.
            - See a small sensitivity matrix (WACC vs terminal growth).
            """)
        st.markdown(
            f"**Data source (uploaded file):** `sandbox:/mnt/data/mock_data.json`"
        )
        st.write("---")

        # ------------------------------
        # Data seed (attempt to pull seed FCF from uploaded data)
        # ------------------------------
        df_metrics = pd.DataFrame(self.state.metrics_df.sort_values("date")) if self.state.metrics_df is not None else pd.DataFrame()
        df_cash = pd.DataFrame(self.state.cashflow_df.sort_values("date")) if self.state.cashflow_df is not None else pd.DataFrame()
        st.caption("This playground will attempt to use `metrics.freeCashFlowToFirm` or `cashflow.freeCashFlow` as the seed FCF if available.")

        seed_fcf = None
        if not df_metrics.empty and "freeCashFlowToFirm" in df_metrics.columns:
            try:
                seed_fcf = float(df_metrics.iloc[-1]["freeCashFlowToFirm"])
            except Exception:
                seed_fcf = None
        if seed_fcf is None and not df_cash.empty and "freeCashFlow" in df_cash.columns:
            try:
                seed_fcf = float(df_cash.iloc[-1]["freeCashFlow"])
            except Exception:
                seed_fcf = None

        # ------------------------------
        # User inputs: DCF horizon and base settings
        # ------------------------------
        st.header("1) Modular DCF Inputs (1 — 10 years)")

        proj_years = st.slider("Projection years", min_value=1, max_value=10, value=5, step=1,
                               help="Choose the number of explicit forecast years (min 1, max 10).")

        # dynamic FCF input grid
        st.write("Enter Free Cash Flow (FCF) for each projected year (units: same as dataset):")
        # create columns across the screen for compact layout
        cols = st.columns(5)
        fcf_inputs = []
        default_base = seed_fcf if seed_fcf is not None else 50.0
        for i in range(proj_years):
            col = cols[i % 5]
            default_val = float(default_base * (1 + 0.05 * i)) if seed_fcf is not None else float(default_base + i * 5)
            val = col.number_input(f"FCF Y{i+1}", key=f"fcf_{i+1}", value=round(default_val, 2), step=0.1)
            fcf_inputs.append(float(val))

        FCFs = np.array(fcf_inputs, dtype=float)

        st.write("---")
        st.header("2) Discount & Terminal Settings")

        left, mid, right = st.columns(3)
        with left:
            wacc = st.number_input("WACC / Discount rate (%)", value=8.0, min_value=0.1, max_value=50.0, step=0.1) / 100.0
            st.caption("Used to discount projected FCF and terminal value.")
        with mid:
            terminal_method = st.selectbox("Terminal method", ["Perpetuity (g)", "Terminal multiple"])
        with right:
            if terminal_method == "Perpetuity (g)":
                term_g = st.number_input("Terminal growth g (%)", value=2.0, step=0.1, min_value=-5.0, max_value=10.0) / 100.0
                term_mult = None
            else:
                term_mult = st.number_input("Terminal EV / FCF multiple", value=12.0, step=0.5, min_value=1.0, max_value=100.0)
                term_g = None

        # extra operating assumptions (optional)
        st.write("Optional operating assumptions (only used if you want to derive FCF from revenue or margins):")
        with st.expander("Advanced operating assumptions (not required)"):
            _use_margin_model = st.checkbox("Assume FCF margin approach (instead of entering FCF directly)", value=False)
            if _use_margin_model:
                revenue = st.number_input("Base revenue (latest)", value=1000.0, step=1.0)
                fcf_margin = st.number_input("FCF margin (FCF / Revenue %)", value=0.05, step=0.01) / 100.0
                # optional: if user toggles, override FCFs with margin-derived
                if st.button("Apply margin -> FCF for projection"):
                    for i in range(proj_years):
                        FCFs[i] = revenue * (1 + 0.03) ** (i + 1) * fcf_margin
                    st.success("FCF overwritten with margin-driven projection.")

        st.write("---")
        st.header("3) Scenario Presets (one-click) — Mild scenarios")

        sc1, sc2, sc3 = st.columns(3)
        if sc1.button("Conservative"):
            # damp growth and increase WACC
            FCFs = FCFs * 0.9
            wacc = min(wacc * 1.15, 0.4)
            if term_g is not None:
                term_g = term_g * 0.7
            st.success("Conservative scenario applied.")
        if sc2.button("Base"):
            st.info("Base scenario: no change.")
        if sc3.button("Optimistic"):
            FCFs = FCFs * 1.12
            wacc = max(wacc * 0.9, 0.02)
            if term_g is not None:
                term_g = term_g * 1.3
            st.success("Optimistic scenario applied.")

        st.write("---")

        # ------------------------------
        # DCF calculation
        # ------------------------------
        st.header("4) DCF Results & Interpretation (with charts)")

        if wacc <= (term_g if term_g is not None else -np.inf):
            st.error("WACC must exceed terminal growth g for a valid perpetuity terminal value.")
        else:
            years = np.arange(1, proj_years + 1)
            discount_factors = (1 + wacc) ** years
            pv_fcfs = FCFs / discount_factors

            # terminal value
            if terminal_method == "Perpetuity (g)":
                terminal_fcf = FCFs[-1] * (1 + term_g)
                terminal_value = terminal_fcf / (wacc - term_g)
            else:
                terminal_value = FCFs[-1] * term_mult

            pv_terminal = terminal_value / ((1 + wacc) ** proj_years)

            EV_dcf = pv_fcfs.sum() + pv_terminal

            st.subheader("Numeric Results")
            st.write(f"- PV of projected FCF (years 1..{proj_years}): **${pv_fcfs.sum():,.2f}**")
            st.write(f"- PV of terminal: **${pv_terminal:,.2f}**")
            st.write(f"- **Enterprise Value (DCF)** = **${EV_dcf:,.2f}**")

            # balance sheet adjustments
            st.write("---")
            st.subheader("Adjust to Equity Value / Per-share (optional)")
            debt = st.number_input("Net Debt (debt - cash) or Total Debt (same units as FCF)", value=0.0, step=1.0)
            shares = st.number_input("Shares outstanding (same units as FCF units / share)", value=1.0, step=1.0)
            equity_value = EV_dcf - debt
            per_share = equity_value / shares if shares and shares > 0 else np.nan

            st.metric("Implied Enterprise Value", f"${EV_dcf:,.2f}")
            st.metric("Implied Equity Value", f"${equity_value:,.2f}")
            if not np.isnan(per_share):
                st.metric("Implied per-share value", f"${per_share:,.4f}")

            # ------------------------------
            # Charts: Projected FCF (line & bar) and PV waterfall
            # ------------------------------
            st.write("---")
            st.subheader("Charts: FCF Projection & PV Waterfall")

            # projection line + bar
            df_proj = pd.DataFrame({
                "year": years,
                "FCF": FCFs,
                "PV(FCF)": pv_fcfs
            })

            fig_proj = go.Figure()
            fig_proj.add_trace(go.Bar(x=df_proj["year"], y=df_proj["FCF"], name="FCF (nominal)"))
            fig_proj.add_trace(go.Line(x=df_proj["year"], y=df_proj["FCF"], name="FCF (trend)", yaxis="y1",
                                       line=dict(dash="dash")))
            fig_proj.update_layout(title="Projected FCF (nominal)", xaxis_title="Year", yaxis_title="FCF")
            st.plotly_chart(fig_proj, use_container_width=True)

            # PV waterfall: each PV of FCF as relative, terminal as total (final)
            waterfall_y = list(pv_fcfs)
            waterfall_measure = ["relative"] * len(pv_fcfs)
            labels = [f"Y{yr}" for yr in years]

            # append terminal as a total
            waterfall_y.append(pv_terminal)
            waterfall_measure.append("total")
            labels.append("Terminal (PV)")

            fig_wf = go.Figure(go.Waterfall(
                name="DCF PV",
                orientation="v",
                measure=waterfall_measure,
                x=labels,
                y=waterfall_y,
                connector={"line": {"color": "rgb(120,120,120)"}},
                decreasing={"marker": {"color": "firebrick"}},
                increasing={"marker": {"color": "forestgreen"}},
                totals={"marker": {"color": "blue"}}
            ))
            fig_wf.update_layout(title="DCF PV Waterfall (contribution of each year's discounted cash flows)", xaxis_title="", yaxis_title="USD")
            st.plotly_chart(fig_wf, use_container_width=True)

            # Combined chart: PV(FCF) stacked bars + PV Terminal overlay line
            fig_comb = go.Figure()
            fig_comb.add_trace(go.Bar(x=df_proj["year"], y=df_proj["PV(FCF)"], name="PV(FCF)"))
            fig_comb.add_trace(go.Bar(x=[proj_years + 1], y=[pv_terminal], name="PV(Terminal)"))
            fig_comb.update_layout(title="PV contributions: Years + Terminal", xaxis_title="Year / Terminal", yaxis_title="PV (USD)", barmode="stack")
            st.plotly_chart(fig_comb, use_container_width=True)

            # ------------------------------
            # Sensitivity matrix (small)
            # ------------------------------
            st.write("---")
            st.subheader("Sensitivity: WACC vs Terminal growth (small grid)")

            # generate small grids around chosen WACC and terminal g
            wacc_vals = np.array([wacc * 0.95, wacc, wacc * 1.05])
            if terminal_method == "Perpetuity (g)":
                g_base = term_g
                g_vals = np.array([g_base - 0.01, g_base, g_base + 0.01])
            else:
                # if terminal multiple, vary multiple a bit
                mult_base = term_mult
                g_vals = np.array([mult_base * 0.9, mult_base, mult_base * 1.1])

            sens_index = []
            sens_cols = []
            sens_df = pd.DataFrame(index=[f"{g:.2%}" for g in g_vals], columns=[f"{w:.2%}" for w in wacc_vals])

            for w in wacc_vals:
                for idx, gval in enumerate(g_vals):
                    if terminal_method == "Perpetuity (g)":
                        if w <= gval:
                            sens_df.at[f"{gval:.2%}", f"{w:.2%}"] = np.nan
                        else:
                            # compute pv with these params (terminal as perpetuity)
                            discount_factors_local = (1 + w) ** years
                            pv_local = (FCFs / discount_factors_local).sum()
                            term_fcf_local = FCFs[-1] * (1 + gval)
                            term_local = term_fcf_local / (w - gval)
                            pv_term_local = term_local / ((1 + w) ** proj_years)
                            sens_df.at[f"{gval:.2%}", f"{w:.2%}"] = pv_local + pv_term_local
                    else:
                        # treat gval as terminal multiple
                        discount_factors_local = (1 + w) ** years
                        pv_local = (FCFs / discount_factors_local).sum()
                        term_local = FCFs[-1] * gval
                        pv_term_local = term_local / ((1 + w) ** proj_years)
                        sens_df.at[f"{gval:.2%}", f"{w:.2%}"] = pv_local + pv_term_local

            # format sens_df nicely
            st.dataframe(sens_df.style.format("${:,.0f}"))

            st.write("---")
            st.markdown("**Interpretation notes:**")
            st.markdown(
                """
                - The **PV waterfall** shows how each year's discounted cash flow contributes to the total enterprise value;
                  the terminal PV is often the largest chunk — confirm sensitivity to the terminal assumption.
                - Use the **sensitivity grid** to understand how small changes in WACC or terminal assumptions move enterprise value.
                - Always check units (millions vs. thousands vs. single $) and ensure debt/shares are in the same units before deriving per-share values.
                """
            )

        st.write("---")
        st.markdown("**Developer note:** Playground reads data (if present) from the uploaded file at `sandbox:/mnt/data/mock_data.json` to attempt to seed FCF. You can still override all inputs manually.")
