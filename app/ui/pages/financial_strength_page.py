"""
Financial Strength Page
"""
import streamlit as st
from app.ui.base_page import BasePage

class FinancialStrengthPage(BasePage):
    def render(self):
        st.header('Financial Strength')
        st.write('Liquidity, leverage and coverage metrics')

        if self.state.metrics_df is None or self.state.metrics_df.empty:
            st.info('Upload balance sheet to compute leverage and liquidity ratios.')
            return

        cols = st.columns(3)
        latest = self.state.metrics_df.iloc[-1]
        cols[0].metric('Latest Cash (B)', self.service.format_b(latest['cashAndCashEquivalents']))
        cols[1].metric('Debt to Equity', f"{latest['debt_to_equity']:.2f}")
        cols[2].metric('Current ratio', f"{latest['current_ratio']:.2f}")
