"""
Narrative Generator Page
"""
import streamlit as st
from app.ui.base_page import BasePage

class NarrativeGeneratorPage(BasePage):
    def render(self):
        st.header('Narrative Generator')
        st.write('Auto-generated narrative from computed metrics. Edit or export the narrative as text.')

        if self.state.metrics_df is None or self.state.metrics_df.empty:
            st.info('Upload data to generate a narrative.')
            return

        latest = self.state.metrics_df.iloc[-1]
        lines = []
        lines.append(f"Executive summary — Fiscal Year {int(latest['fiscalYear'])}:")
        lines.append(f"Apple generated {self.service.format_b(latest['freeCashFlow'])} of free cash flow in the latest fiscal year, with operating cash flow of {self.service.format_b(latest['operatingCashFlow'])} and net income of {self.service.format_b(latest['netIncome'])}.")
        ocf_ratio = latest['OCF_to_NetIncome']
        if ocf_ratio is not None:
            lines.append(f"Cash conversion (OCF / Net Income) was {ocf_ratio:.2f}x, indicating {'strong' if ocf_ratio>1.0 else 'weaker'} earnings quality.")
        if 'payout_pct_of_FCF' in latest and latest['payout_pct_of_FCF'] is not None:
            lines.append(f"Management returned {latest['payout_pct_of_FCF']*100:.1f}% of FCF to shareholders via buybacks and dividends in the year.")
        if 'netDebt' in latest and latest['netDebt'] is not None:
            lines.append(f"Net debt stands at {self.service.format_b(latest['netDebt'])}.")
        if 'changeInWorkingCapital' in latest and latest['changeInWorkingCapital'] is not None:
            delta_wc = latest['changeInWorkingCapital']
            if delta_wc < 0:
                lines.append(f"Working capital change was a headwind to cash flow of {self.service.format_b(delta_wc)} (cash outflow).")
            else:
                lines.append(f"Working capital supported cash flow by {self.service.format_b(delta_wc)} (cash inflow).")
        if 'capitalExpenditure' in latest and latest['capitalExpenditure'] is not None:
            lines.append(f"Capital expenditure was {self.service.format_b(latest['capitalExpenditure'])}, representing {latest['capex_to_revenue']*100:.2f}% of revenue (if revenue data provided)." )
        lines.append('Key risks include sustained increases in working capital requirements, larger-than-expected capex, or slowing revenue growth which would reduce FCF. Upside comes from margin expansion or services growth.')

        narrative = ' '.join(lines)
        narrative = st.text_area('Auto-generated narrative (editable)', value=narrative, height=300)
        st.download_button('Download narrative', data=narrative, file_name='aapl_narrative.txt', mime='text/plain')
