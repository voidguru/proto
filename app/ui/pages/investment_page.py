"""
Investment Page
"""
import streamlit as st
from app.ui.base_page import BasePage

class InvestmentPage(BasePage):
    def render(self):
        st.header('Investment Engine')
        st.write('CapEx, R&D (if available), and cash ROIC.')

        if self.state.metrics_df is None or self.state.metrics_df.empty:
            st.info('Upload data to analyze investment engine.')
            return

        st.subheader('CapEx vs Revenue')
        st.line_chart(self.state.metrics_df.set_index('fiscalYear')[['capitalExpenditure','revenue']].apply(lambda x: x/1e9))

        st.subheader('CapEx / Revenue')
        st.line_chart(self.state.metrics_df.set_index('fiscalYear')['capex_to_revenue'])
