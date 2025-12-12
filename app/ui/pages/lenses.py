"""
Lenses Page — Multi-period Income Statement Waterfalls
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.ui.base_page import BasePage


class LensesPage(BasePage):
    def build_yoy_waterfall(self, df_row_now, df_row_prev, available_fields, height=450):
        """
        Create YoY change waterfall:
        Δ = current - previous for each available field
        """
        x = []
        y = []
        measures = []

        for col, label in available_fields:
            now_val = df_row_now.get(col, None)
            prev_val = df_row_prev.get(col, None)

            if (now_val is None or pd.isna(now_val)) or (prev_val is None or pd.isna(prev_val)):
                continue

            delta = now_val - prev_val

            x.append(label.replace("-", "Δ "))  # label cleanup
            y.append(delta)
            measures.append("relative")

        # Total: if netIncome exists
        if "netIncome" in df_row_now and not pd.isna(df_row_now["netIncome"]) and not pd.isna(df_row_prev["netIncome"]):
            net_delta = df_row_now["netIncome"] - df_row_prev["netIncome"]
            x.append("Δ Net Income (Final)")
            y.append(net_delta)
            measures.append("total")

        fig = go.Figure(go.Waterfall(
            name="YoY Change",
            orientation="v",
            measure=measures,
            x=x,
            y=y,
            connector={"line": {"color": "rgb(100,100,100)"}}
        ))

        fig.update_layout(
            title="YoY Change Waterfall",
            height=height,
            showlegend=False,
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis_title="Line Item",
            yaxis_title="Δ Amount (YoY)"
        )

        return fig

    def render(self):
        st.header("Lenses — Income Statement Breakdowns")

        # Load the income statement
        df_is = pd.DataFrame(self.state.income_statement_df)
        if df_is.empty:
            st.warning("No income_statement data found.")
            return

        # sort chronologically
        df_is = df_is.sort_values("date")
        df_is["date"] = pd.to_datetime(df_is["date"])

        st.write("""
        This page provides **Income Statement waterfall plots** for every reporting period available.
        
        The waterfall decomposition uses *only the fields that actually exist in your dataset*.
        """)

        st.write("---")

        # Identify usable income statement fields
        # We map them into logical order if available:
        field_order = [
            ("revenue", "Revenue"),
            ("costOfRevenue", "- Cost of Revenue"),
            ("grossProfit", "Gross Profit"),
            ("operatingExpenses", "- Operating Expenses"),
            ("sellingGeneralAndAdministrative", "- SG&A"),
            ("researchAndDevelopment", "- R&D"),
            ("otherOperatingExpenses", "- Other OpEx"),
            ("operatingIncome", "Operating Income"),
            ("netInterestIncome", "Net Interest Income"),
            ("interestExpense", "- Interest Expense"),
            ("incomeBeforeTax", "Income Before Tax"),
            ("incomeTaxExpense", "- Income Tax"),
            ("netIncome", "Net Income"),
        ]

        available_fields = [(col, label) for col, label in field_order if col in df_is.columns]

        # Let the user pick a period, or cycle through all
        st.subheader("Select reporting period")
        period = st.selectbox(
            "Choose a date",
            df_is["date"].dt.strftime("%Y-%m-%d").tolist()
        )

        df_single = df_is[df_is["date"] == pd.to_datetime(period)].iloc[0]

        st.write(f"### Income Statement Waterfall for {period}")

        fig = self.build_income_statement_waterfall(df_single, available_fields)
        st.plotly_chart(fig, use_container_width=True)

        st.write("---")

        # ---------------------------------------------
        # ALL PERIODS YoY CHANGE — Waterfall Grid
        # ---------------------------------------------
        st.subheader("All Periods — YoY Change Waterfall Grid")

        st.write("""
        Each chart shows how **each income statement line item moved vs the previous period**.
        Positive = favorable change, Negative = deterioration.
        """)

        if len(df_is) < 2:
            st.info("Need at least 2 periods to compute YoY changes.")
        else:
            for i in range(1, len(df_is)):
                now_row = df_is.iloc[i]
                prev_row = df_is.iloc[i-1]

                date_now = now_row["date"].strftime("%Y-%m-%d")
                date_prev = prev_row["date"].strftime("%Y-%m-%d")

                st.markdown(f"### {date_now} vs {date_prev}")

                fig_yoy = self.build_yoy_waterfall(now_row, prev_row, available_fields)
                st.plotly_chart(fig_yoy)

                st.write("---")


    # ------------------------------------------------------------------
    # Build waterfall helper function
    # ------------------------------------------------------------------
    def build_income_statement_waterfall(self, row, available_fields, height=500):
        """
        Generate a Plotly waterfall for one reporting date.
        Only includes fields that exist in dataset.
        """
        x = []
        y = []
        measures = []

        # Build step-by-step
        running_total = 0

        for col, label in available_fields:
            val = row.get(col, None)
            if val is None or pd.isna(val):
                continue

            # For negative items, ensure waterfall direction is correct:
            if col.lower().startswith(("cost", "expense", "selling", "research", "interestexpense", "incometax")):
                # treat as negative contribution
                delta = -abs(val)
            else:
                delta = val

            x.append(label)
            y.append(delta)
            measures.append("relative")

        # Add final total if netIncome exists
        if "netIncome" in row and not pd.isna(row["netIncome"]):
            x.append("Net Income (Final)")
            y.append(row["netIncome"])
            measures.append("total")

        fig = go.Figure(go.Waterfall(
            name="Income Statement",
            orientation="v",
            measure=measures,
            x=x,
            y=y,
            connector={"line": {"color": "rgb(120,120,120)"}}
        ))

        fig.update_layout(
            title="Income Statement Decomposition",
            height=height,
            showlegend=False,
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis_title="Line Item",
            yaxis_title="Amount (USD)"
        )

        return fig
