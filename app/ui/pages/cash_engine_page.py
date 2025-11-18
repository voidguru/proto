"""
Cash Engine Page
"""
import streamlit as st
import plotly.graph_objects as go
from app.ui.base_page import BasePage
from decimal import Decimal

class CashEnginePage(BasePage):
    def render(self):
        st.header('Cash Engine')
        st.write('Operating cash flow quality, working capital, and cash bridges.')

        if self.state.metrics_df is None or self.state.metrics_df.empty:
            st.info('Upload cashflow statement for cash engine analysis.')
            return

        st.subheader('OCF / Net Income')
        st.line_chart(self.state.metrics_df.set_index('fiscalYear')['OCF_to_NetIncome'])

        st.subheader('FCF Bridge (OCF -> CapEx -> FCF)')
        years = self.state.metrics_df['fiscalYear'].astype(str).tolist()
        wf = go.Figure()
        wf.add_trace(go.Bar(
            x=years,
            y=(self.state.metrics_df['operatingCashFlow'] / Decimal(1e9)),
            name='OCF'
        ))
        wf.add_trace(go.Bar(
            x=years,
            y=(self.state.metrics_df['capitalExpenditure'] / Decimal(1e9)),
            name='CapEx'
        ))
        wf.add_trace(go.Bar(
            x=years,
            y=(self.state.metrics_df['freeCashFlow'] / Decimal(1e9)),
            name='FCF'
        ))
        wf.update_layout(
            barmode='group',
            height=420,
            yaxis_title='Billions USD'
        )
        st.plotly_chart(wf, use_container_width=True)

        st.subheader('Working Capital (change)')
        if 'changeInWorkingCapital' in self.state.metrics_df.columns:
            st.bar_chart(self.state.metrics_df.set_index('fiscalYear')['changeInWorkingCapital'].apply(lambda x: x/1e9))
