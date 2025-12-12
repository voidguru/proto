"""
Capital Allocation Page
"""
import streamlit as st
from app.ui.base_page import BasePage

class CapitalAllocationPage(BasePage):
    def render(self):
        st.header('Capital Allocation')
        st.write('Buybacks, dividends, debt activity and payout ratios')

        if self.state.metrics_df is None or self.state.metrics_df.empty:
            st.info('Upload cashflow and balance sheet to enable capital allocation analysis.')
            return

        st.subheader('Buybacks & Dividends (B)')
        bd = self.state.metrics_df.set_index('fiscalYear')[['buybacks','dividends']].apply(lambda x: x/(1e9))
        st.bar_chart(bd)

        st.subheader('Payout ratio (Buybacks+Dividends) / FCF')
        st.line_chart(self.state.metrics_df.set_index('fiscalYear')['payout_pct_of_FCF'])

        st.subheader('Net Debt')
        st.line_chart(self.state.metrics_df.set_index('fiscalYear')['netDebt'].apply(lambda x: x/(1e9)))
