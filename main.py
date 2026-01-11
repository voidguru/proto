"""
Main application file for the Streamlit app.
"""
import streamlit as st
from app.state.app_state import AppState
from app.services.financial_data_service import FinancialDataService
from app.repositories.financial_data_repository import FinancialDataRepository
from app.ui.page_factory import PageFactory
from app.config import settings
import pandas as pd
import json

st.set_page_config(page_title="The Gift", layout="wide")

def main():
    state = AppState()
    repository = FinancialDataRepository(table_name="FinancialStatements", api_key=settings.API_KEY)
    service = FinancialDataService(repository)

    st.title("To you, my dear companion")
    st.markdown("May this little gist awaken your will.")

    st.sidebar.header("Ticker Selector")
    upload_option = st.sidebar.radio("", options=['AAPL demo', 'API'])

    if upload_option == 'API':
        symbol_input = st.sidebar.selectbox("Select Stock Symbol:", options=settings.ALLOWED_SYMBOLS, index=settings.ALLOWED_SYMBOLS.index(state.symbol) if state.symbol in settings.ALLOWED_SYMBOLS else 0)
        if st.sidebar.button("Fetch Data"):
            if symbol_input:
                bs, is_, cf, metrics, financials = service.get_financial_statements(symbol_input)
                bs_df, is_df, cf_df, metrics_df, financials_df = service.convert_to_dataframes(bs, is_, cf, metrics, financials)
                state.balance_sheet_df = bs_df
                state.income_statement_df = is_df
                state.cashflow_df = cf_df
                state.metrics_df = metrics_df
                state.financials_df = financials_df
                state.symbol = symbol_input
    elif upload_option == 'AAPL demo':
        with open("data/mock_data.json", "r") as f:
            raw = json.load(f)
        bs_models, is_models, cf_models, metrics_models, financials = service.load_mock_data("data/mock_data.json")
        bs_df, is_df, cf_df, metrics_df, financials_df = service.convert_to_dataframes(bs_models, is_models, cf_models, metrics_models, financials)
        state.balance_sheet_df = bs_df
        state.income_statement_df = is_df
        state.cashflow_df = cf_df
        state.metrics_df = metrics_df
        state.financials_df = financials_df

    if state.metrics_df is not None and not state.metrics_df.empty:
        tabs = st.tabs(list(PageFactory.PAGES.keys()))
        for i, tab_name in enumerate(PageFactory.PAGES.keys()):
            with tabs[i]:
                page = PageFactory.create_page(tab_name, state, service)
                page.render()

if __name__ == "__main__":
    main()
