"""
Centralized state management for the Streamlit application.
This class provides a clean, typed interface to st.session_state,
preventing direct access and ensuring consistency.
"""
import streamlit as st
from typing import Any, Optional
import pandas as pd

class AppState:
    """
    A wrapper around st.session_state to provide a structured way to manage state.
    """
    def __init__(self):
        if "cf_df" not in st.session_state:
            st.session_state.cf_df = None
        if "metrics_df" not in st.session_state:
            st.session_state.metrics_df = None
        if "is_df" not in st.session_state:
            st.session_state.is_df = None
        if "bs_df" not in st.session_state:
            st.session_state.bs_df = None
        if "symbol" not in st.session_state:
            st.session_state.symbol = ""
        if "financials_df" not in st.session_state:
            st.session_state.financials_df = None
                

    def get(self, key: str) -> Any:
        """Gets a value from the session state."""
        return st.session_state.get(key)

    def set(self, key: str, value: Any) -> None:
        """Sets a value in the session state."""
        st.session_state[key] = value

    @property
    def cashflow_df(self) -> Optional[pd.DataFrame]:
        return self.get("cf_df")

    @cashflow_df.setter
    def cashflow_df(self, value: pd.DataFrame):
        self.set("cf_df", value)

    @property
    def financials_df(self) -> Optional[pd.DataFrame]:
        return self.get("financials_df")

    @financials_df.setter
    def financials_df(self, value: pd.DataFrame):
        self.set("financials_df", value)

    @property
    def metrics_df(self) -> Optional[pd.DataFrame]:
        return self.get("metrics_df")

    @metrics_df.setter
    def metrics_df(self, value: pd.DataFrame):
        self.set("metrics_df", value)

    @property
    def income_statement_df(self) -> Optional[pd.DataFrame]:
        return self.get("is_df")

    @income_statement_df.setter
    def income_statement_df(self, value: pd.DataFrame):
        self.set("is_df", value)

    @property
    def balance_sheet_df(self) -> Optional[pd.DataFrame]:
        return self.get("bs_df")

    @balance_sheet_df.setter
    def balance_sheet_df(self, value: pd.DataFrame):
        self.set("bs_df", value)

    @property
    def symbol(self) -> str:
        return self.get("symbol")

    @symbol.setter
    def symbol(self, value: str):
        self.set("symbol", value)

    def clear(self):
        """Clears the session state."""
        st.session_state.clear()
