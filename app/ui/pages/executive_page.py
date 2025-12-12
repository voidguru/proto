"""
Executive Summary Page
"""
import streamlit as st
from app.ui.base_page import BasePage
from decimal import Decimal

class ExecutivePage(BasePage):
    def render(self):
        st.header("Executive Overview")
        st.write("High-level summary of cashflow, profitability and capital allocation. For a complete narrative upload income & balance data.")

        if self.state.metrics_df is None or self.state.metrics_df.empty:
            st.info("No prepared metrics available. Upload income, balance and cashflow files and press 'Validate & Prepare Data'.")
            return

        cols = st.columns(4)
        latest = self.state.metrics_df.iloc[-1]
        cols[0].metric("Latest FCF (B)", self.service.format_b(latest['freeCashFlow'] / Decimal(1e9)))
        cols[1].metric("Latest OCF (B)", self.service.format_b(latest['operatingCashFlow'] / Decimal(1e9)))
        cols[2].metric("Latest Net Income (B)", self.service.format_b(latest['netIncome'] / Decimal(1e9)))
        cols[3].metric("Net Debt (B)", self.service.format_b(latest['netDebt'] / Decimal(1e9)))

        st.subheader('Trend — Revenue / Net Income / OCF / FCF')
        plot_df = self.state.metrics_df.set_index('fiscalYear')[['revenue','netIncome','operatingCashFlow','freeCashFlow']]
        st.line_chart(plot_df.apply(lambda x: x/Decimal(1e9)))
