"""
Page Factory for creating and managing pages in the application.
"""
from app.ui.pages.meta import ValuationProblemsPage
from app.ui.pages.lenses import LensesPage
from app.ui.pages.executive_page import ExecutivePage
from app.ui.pages.profit_engine_page import ProfitEnginePage
from app.ui.pages.cash_engine_page import CashEnginePage
from app.ui.pages.investment_page import InvestmentPage
from app.ui.pages.capital_allocation_page import CapitalAllocationPage
from app.ui.pages.financial_strength_page import FinancialStrengthPage
from app.ui.pages.valuation_page import ValuationPage
from app.ui.pages.narrative_generator_page import NarrativeGeneratorPage
from app.ui.pages.data_page import DataPage
from app.state.app_state import AppState
from app.services.financial_data_service import FinancialDataService

class PageFactory:
    PAGES = {
        "Executive": ExecutivePage,
        "Profit Engine": ProfitEnginePage,
        "Cash Engine": CashEnginePage,
        "Investment": InvestmentPage,
        "Capital Allocation": CapitalAllocationPage,
        "Financial Strength": FinancialStrengthPage,
        "Valuation": ValuationPage,
        # "Narrative Generator": NarrativeGeneratorPage,
        # "Data": DataPage,
        "Lenses": LensesPage,
        "Textbook": ValuationProblemsPage
    }

    @staticmethod
    def create_page(page_name: str, state: AppState, service: FinancialDataService):
        page_class = PageFactory.PAGES.get(page_name)
        if page_class:
            return page_class(state, service)
        else:
            raise ValueError(f"Page '{page_name}' not found.")
