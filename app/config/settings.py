"""
Application-wide settings and constants.
"""
import streamlit as st

ALLOWED_SYMBOLS = [
    "AAPL", "TSLA", "AMZN", "MSFT", "NVDA", "GOOGL", "META", "NFLX", "JPM", "V", "BAC", "AMD", "PYPL",
    "DIS", "T", "PFE", "COST", "INTC", "KO", "TGT", "NKE", "SPY", "BA", "BABA", "XOM", "WMT", "GE", "CSCO",
    "VZ", "JNJ", "CVX", "PLTR", "SQ", "SHOP", "SBUX", "SOFI", "HOOD", "RBLX", "SNAP", "UBER", "FDX", "ABBV",
    "ETSY", "MRNA", "LMT", "GM", "F", "RIVN", "LCID", "CCL", "DAL", "UAL", "AAL", "TSM", "SONY", "ET", "NOK",
    "MRO", "COIN", "SIRI", "RIOT", "CPRX", "VWO", "SPYG", "ROKU", "VIAC", "ATVI", "BIDU", "DOCU", "ZM", "PINS",
    "TLRY", "WBA", "MGM", "NIO", "C", "GS", "WFC", "ADBE", "PEP", "UNH", "CARR", "FUBO", "HCA", "TWTR", "BILI",
    "RKT"
]

def get_api_key():
    try:
        return st.secrets["API_KEY"]
    except FileNotFoundError:
        # For local development without a secrets.toml file
        return "SasT1HkUMNVFoRdQqorB8GXlZ0q6KDuE"

API_KEY = get_api_key()
