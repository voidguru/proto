"""
Profit Engine Page
"""
import streamlit as st
import plotly.graph_objects as go
from app.ui.base_page import BasePage

class ProfitEnginePage(BasePage):
    def render(self):
        st.header('Profit Engine')
        st.write('Revenue growth, margins and operating leverage.')

        if self.state.metrics_df is None or self.state.metrics_df.empty:
            st.info('Upload income statement to view profit engine.')
            return

        # Margins
        metrics_df = self.state.metrics_df
        metrics_df['grossMargin'] = metrics_df['grossProfit'] / metrics_df['revenue']
        metrics_df['opMargin'] = metrics_df['operatingIncome'] / metrics_df['revenue']
        metrics_df['netMargin'] = metrics_df['netIncome'] / metrics_df['revenue']

        fig = go.Figure()
        fig.add_trace(go.Bar(x=metrics_df['fiscalYear'], y=metrics_df['grossMargin'], name='Gross Margin'))
        fig.add_trace(go.Bar(x=metrics_df['fiscalYear'], y=metrics_df['opMargin'], name='Operating Margin'))
        fig.add_trace(go.Bar(x=metrics_df['fiscalYear'], y=metrics_df['netMargin'], name='Net Margin'))
        fig.update_layout(barmode='group', yaxis_tickformat=',.0%', height=420)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader('Revenue growth')
        metrics_df['rev_yoy'] = metrics_df['revenue'].pct_change()
        st.bar_chart(metrics_df.set_index('fiscalYear')['rev_yoy'].apply(lambda x: x*100))
