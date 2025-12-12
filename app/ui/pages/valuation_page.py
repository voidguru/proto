"""
Valuation Page
"""
import streamlit as st
import numpy as np
from app.ui.base_page import BasePage
from decimal import Decimal

class ValuationPage(BasePage):
    def render(self):
        st.header('Valuation')
        st.write('DCF (scenario) and relative valuation based on FCF if market data provided.')

        if self.state.metrics_df is None or self.state.metrics_df.empty:
            st.info('Upload statements and provide market data (market cap/price/shares) for valuation.')
            return

        latest_fcf = self.state.metrics_df.iloc[-1]['freeCashFlow']
        st.write(f"Last reported FCF: **{self.service.format_b(latest_fcf)}**")

        # DCF inputs
        r = st.number_input('Discount rate (WACC %)', value=8.0)
        growth = st.number_input('Base FCF growth % p.a.', value=3.0)
        years = st.slider('Forecast years', min_value=3, max_value=20, value=5)
        term_g = st.number_input('Terminal growth %', value=2.0)
        shares = st.number_input('Shares outstanding (in billions)', value=15.8)

        # compute
        fcf0 = latest_fcf
        g = growth/100.0
        rdec = r/100.0
        fcf_proj = [fcf0 * Decimal((1+g)**i) for i in range(1, years+1)]
        pv = [fcf_proj[i]/(Decimal(1+rdec)**Decimal(i+1)) for i in range(len(fcf_proj))]
        tv = fcf_proj[-1]*Decimal(1+term_g/100.0)/Decimal(rdec-term_g/100.0) if rdec>term_g/100.0 else np.nan
        pv_tv = tv/Decimal((1+rdec)**years) if not None else np.nan
        npv = sum(pv) + (pv_tv if pv_tv is not None else 0)
        per_share = npv / Decimal(shares*1e9) if shares>0 else np.nan

        st.metric('Intrinsic NPV (FCF discounted, USD B)', self.service.format_b(npv))
        st.metric('Implied per-share (USD)', f"${per_share:,.2f}" if not None else 'n/a')
