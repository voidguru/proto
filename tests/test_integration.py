"""
Integration tests for the application.
"""
import pytest
from app.state.app_state import AppState
from app.services.financial_data_service import FinancialDataService
from app.repositories.financial_data_repository import FinancialDataRepository
from app.ui.page_factory import PageFactory
from app.config import settings

@pytest.fixture
def app_dependencies(mocker):
    """
    Provides the application dependencies for testing.
    """
    mocker.patch('boto3.resource')
    state = AppState()
    repository = FinancialDataRepository(table_name="FinancialStatements", api_key=settings.API_KEY)
    service = FinancialDataService(repository)
    return state, service

def test_page_factory(app_dependencies):
    """
    Tests that the PageFactory can create all the pages.
    """
    state, service = app_dependencies
    for page_name in PageFactory.PAGES.keys():
        page = PageFactory.create_page(page_name, state, service)
        assert page is not None
