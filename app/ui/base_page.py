"""
Base class for all pages in the Streamlit application.
It provides a common structure and helper methods for all pages.
"""
import streamlit as st
from abc import ABC, abstractmethod
from app.state.app_state import AppState
from app.services.financial_data_service import FinancialDataService

class BasePage(ABC):
    def __init__(self, state: AppState, service: FinancialDataService):
        self.state = state
        self.service = service

    @abstractmethod
    def render(self):
        """
        Renders the page content.
        """
        pass
