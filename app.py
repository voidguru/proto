from decimal import Decimal
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import pandas as pd
from pydantic import ValidationError
from typing import List
import requests

from models import (
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
    KeyMetrics
)
from manager.financial_cache_manager import FinancialCacheManager

allowed_symbols = [
    "AAPL", "TSLA", "AMZN", "MSFT", "NVDA", "GOOGL", "META", "NFLX", "JPM", "V", "BAC", "AMD", "PYPL",
    "DIS", "T", "PFE", "COST", "INTC", "KO", "TGT", "NKE", "SPY", "BA", "BABA", "XOM", "WMT", "GE", "CSCO",
    "VZ", "JNJ", "CVX", "PLTR", "SQ", "SHOP", "SBUX", "SOFI", "HOOD", "RBLX", "SNAP", "UBER", "FDX", "ABBV",
    "ETSY", "MRNA", "LMT", "GM", "F", "RIVN", "LCID", "CCL", "DAL", "UAL", "AAL", "TSM", "SONY", "ET", "NOK",
    "MRO", "COIN", "SIRI", "RIOT", "CPRX", "VWO", "SPYG", "ROKU", "VIAC", "ATVI", "BIDU", "DOCU", "ZM", "PINS",
    "TLRY", "WBA", "MGM", "NIO", "C", "GS", "WFC", "ADBE", "PEP", "UNH", "CARR", "FUBO", "HCA", "TWTR", "BILI",
    "RKT"
]
st.set_page_config(page_title="AAPL Cashflow Deep Narrative", layout="wide")


# --- Initialize session state ---
if "cf_df" not in st.session_state:
    st.session_state.cf_df = None
if "metrics_df" not in st.session_state:
    st.session_state.metrics_df = None
if "is_df" not in st.session_state:
    st.session_state.is_df = ""
if "bs_df" not in st.session_state:
    st.session_state.bs_df = None
if "symbol" not in st.session_state:
    st.session_state.symbol = ""

st.title("Financial Narrative & Visualizer")
st.markdown("This app builds a full narrative + visualization engine from income statement, balance sheet and cashflow data. Upload CSV/JSON/XLSX files (separate or merged), or use the embedded 5-year Apple data to get started.")

# ----------------------
# Utilities & Default Data
# ----------------------
@st.cache_data
def load_default_cashflow():
    # minimal default: the 5-year cashflow data already embedded
    # (For brevity this is abbreviated; the app accepts uploads for full data.)
    return pd.DataFrame()

def convert_to_dataframes(bs_models, is_models, cf_models):
    df_bs = pd.DataFrame([m.dict() for m in bs_models])
    df_is = pd.DataFrame([m.dict() for m in is_models])
    df_cf = pd.DataFrame([m.dict() for m in cf_models])

    # Sort by date descending
    # df_bs = df_bs.sort_values("date", ascending=False)
    # df_is = df_is.sort_values("date", ascending=False)
    # df_cf = df_cf.sort_values("date", ascending=False)

    return df_bs, df_is, df_cf


def load_mock_data(json_path: str):
    with open(json_path, "r") as f:
        raw = json.load(f)

    # Parse balance sheet
    bs_models = []
    for entry in raw["balance_sheet"]:
        try:
            bs_models.append(BalanceSheet(**entry))
        except ValidationError as e:
            print("❌ BalanceSheet validation error:", e)

    # Parse income statement
    is_models = []
    for entry in raw["income_statement"]:
        try:
            is_models.append(IncomeStatement(**entry))
        except ValidationError as e:
            print("❌ IncomeStatement validation error:", e)

    # Parse cash flow statement
    cf_models = []
    for entry in raw["cashflow_statement"]:
        try:
            cf_models.append(CashFlowStatement(**entry))
        except ValidationError as e:
            print("❌ CashFlow validation error:", e)

    return bs_models, is_models, cf_models

def to_b(x):
    return x/1e9


def fmt_b(x):
    try:
        return f"${x/1e9:,.2f}B"
    except Exception:
        return x


# ----------------------
# Data input
# ----------------------
st.sidebar.header("Data input")
upload_option = st.sidebar.radio("How will you provide data?", options=['Use embedded example (AAPL demo)', 'API', 'Upload files (beta)'])

# The app can accept either:
#  - merged long-format file with columns: fiscalYear, statement (income/balance/cashflow), and line items
#  - or 3 separate files: income.csv, balance.csv, cashflow.csv

income_df = pd.DataFrame()
balance_df = pd.DataFrame()
cashflow_df = pd.DataFrame()

if upload_option == 'Upload files (beta)':
    st.sidebar.write("Upload separate files or a single merged file.")
    inc_file = st.sidebar.file_uploader("Income statement (CSV/JSON/XLSX)", type=['csv','json','xlsx'], key='inc')
    bal_file = st.sidebar.file_uploader("Balance sheet (CSV/JSON/XLSX)", type=['csv','json','xlsx'], key='bal')
    cf_file = st.sidebar.file_uploader("Cash flow statement (CSV/JSON/XLSX)", type=['csv','json','xlsx'], key='cf')

    def read_any(file):
        if file is None:
            return pd.DataFrame()
        name = file.name.lower()
        if name.endswith('.csv'):
            return pd.read_csv(file)
        if name.endswith('.json'):
            return pd.read_json(file)
        else:
            return pd.read_excel(file)

    if inc_file is not None:
        income_df = read_any(inc_file)
    if bal_file is not None:
        balance_df = read_any(bal_file)
    if cf_file is not None:
        cashflow_df = read_any(cf_file)

elif upload_option == 'Use embedded example (AAPL demo)':
    st.sidebar.write("Using an embedded demo dataset (Apple). For full narrative upload income and balance sheet for richer metrics.")
    bs_models, is_models, cf_models = load_mock_data("mock_data.json")
    bs_df, is_df, cashflow_df = convert_to_dataframes(bs_models, is_models, cf_models)
    st.session_state.bs_df = bs_df
    st.session_state.is_df = is_df
    st.session_state.cf_df = cashflow_df      
else:
    symbol_input = st.sidebar.selectbox(
                        "Select Stock Symbol:",
                        options=allowed_symbols,
                        index=allowed_symbols.index(st.session_state.symbol) if st.session_state.symbol in allowed_symbols else 0
                    )
    if st.sidebar.button("Fetch Data"):
        if symbol_input:
            # money = st.secrets['API_KEY']
            money = "SasT1HkUMNVFoRdQqorB8GXlZ0q6KDuE"
            try:
                print("EHEHEHHEHE")
                manager = FinancialCacheManager(
                    table_name="FinancialStatements",
                    api_key=money,
                )

                metrics = manager.load(
                    symbol="AAPL",
                    endpoint="key-metrics",
                    model=KeyMetrics,
                    limit=5
                )

                bs = manager.load(
                    symbol="AAPL",
                    endpoint="balance-sheet-statement",
                    model=BalanceSheet,
                    limit=5
                )
                income_statement = manager.load(
                    symbol="AAPL",
                    endpoint="income-statement",
                    model=IncomeStatement,
                    limit=5
                )
                cash_flow_statement = manager.load(
                    symbol="AAPL",
                    endpoint="cash-flow-statement",
                    model=CashFlowStatement,
                    limit=5
                )
                print("VOLEEEEVI")
                balance_df, income_df, cashflow_df = convert_to_dataframes(bs, income_statement, cash_flow_statement)
                cashflow_df = pd.DataFrame(cash_flow_statement)
                cashflow_df = cashflow_df.sort_values("date", ascending=False)
                is_df = pd.DataFrame(income_statement)
                is_df = is_df.sort_values("date", ascending=False)
                metrics_df = pd.DataFrame(metrics)
                metrics_df = metrics_df.sort_values("date", ascending=False)
                bs_df = pd.DataFrame(bs)
                bs_df = bs_df.sort_values("date", ascending=False)

                                # Update session state
                st.session_state.metrics = metrics
                st.session_state.bs_df = bs_df
                st.session_state.is_df = is_df
                st.session_state.cf_df = cashflow_df                
                st.session_state.symbol = symbol_input
            except requests.exceptions.RequestException as e:
                st.error(f"API request failed: {e}")
            except Exception as e:
                st.error(f"Error processing data: {e}")
    st.sidebar.info("There's a daily limit.")

# ----------------------
# Data validation & merging
# ----------------------

# Merge logic: attempt to infer fiscalYear column

def prepare_statement(df, name):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    # try to standardize fiscal year column
    for c in ['fiscalYear','fiscal_year','year','fy','Period']:
        if c in df.columns:
            df['fiscalYear'] = df[c]
            break
    if 'fiscalYear' not in df.columns:
        # try extract from date
        for c in df.columns:
            if 'date' in c.lower():
                try:
                    df['fiscalYear'] = pd.to_datetime(df[c]).dt.year
                    break
                except Exception:
                    pass
    # ensure numeric
    df['fiscalYear'] = pd.to_numeric(df['fiscalYear'], errors='coerce').astype('Int64')
    return df

if st.session_state.bs_df is not None:
    income_df = pd.DataFrame(st.session_state.is_df)
    balance_df = pd.DataFrame(st.session_state.bs_df)
    cashflow_df = pd.DataFrame(st.session_state.cf_df)
    metrics = pd.DataFrame(st.session_state.metrics_df)

    # Minimal check
    have_income = not income_df.empty
    have_balance = not balance_df.empty
    have_cashflow = not cashflow_df.empty

    st.markdown("---")

    # ----------------------
    # Layout: Tabs for chapters
    # ----------------------
    tabs = st.tabs(["Executive","Profit Engine","Cash Engine","Investment","Capital Allocation","Financial Strength","Valuation","Narrative Generator","Data"])

    # Helper: compute unified metrics if we have necessary statements
    @st.cache_data
    def compute_metrics(income, balance, cashflow, metrics):
        # Expect wide-format statements with line-item columns like 'netIncome','revenue','grossProfit','totalAssets','totalLiab', etc.
        # We'll attempt to pull common fields; missing values tolerated.
        df = {}
        years = None
        if not cashflow.empty:
            cf = cashflow.copy()
            cf.columns = list(CashFlowStatement.schema().get("properties").keys())
            cf = cf.sort_values('fiscalYear')
            years = cf['fiscalYear'].dropna().unique().tolist()
        elif not income.empty:
            inc = income.copy()
            inc.columns = list(IncomeStatement.schema().get("properties").keys())
            inc = inc.sort_values('fiscalYear')
            years = inc['fiscalYear'].dropna().unique().tolist()
        elif not balance.empty:
            bal = balance.copy()
            bal.columns = list(BalanceSheet.schema().get("properties").keys())
            bal = bal.sort_values('fiscalYear')
            years = bal['fiscalYear'].dropna().unique().tolist()
        else:
            years = []

        idx = years
        out = pd.DataFrame({'fiscalYear': idx})
        out = out.set_index('fiscalYear')

        def safe_pull(df, col):
            if df is None or df.empty:
                return pd.Series()
            for variant in [col, col.lower(), col.upper(), col.replace(' ','_'), col.replace(' ','').lower()]:
                if variant in df.columns:
                    s = df.set_index('fiscalYear')[variant]
                    s = s.reindex(idx)
                    return s
            return pd.Series([np.nan]*len(idx), index=idx)

        inc = income if not income.empty else None
        bal = balance if not balance.empty else None
        cf = cashflow if not cashflow.empty else None
        out = pd.concat([inc, bal, cf, metrics])
        # derived
        out['netDebt'] = (out['shortTermDebt'].fillna(0) + out['longTermDebt'].fillna(0)) - out['cashAndCashEquivalents'].fillna(0)
        out['buybacks'] = -out['commonStockRepurchased']
        out['dividends'] = -out['commonDividendsPaid']

        # ratios
        out['OCF_to_NetIncome'] = out['operatingCashFlow'] / out['netIncome']
        out['FCF_to_NetIncome'] = out['freeCashFlow'] / out['netIncome']
        out['capex_to_revenue'] = out['capitalExpenditure'] / out['revenue']
        out['buyback_pct_of_FCF'] = out['buybacks'] / out['freeCashFlow']
        out['dividend_pct_of_FCF'] = out['dividends'] / out['freeCashFlow']
        out['payout_pct_of_FCF'] = (out['buybacks'] + out['dividends']) / out['freeCashFlow']
        out['current_ratio'] = out['totalAssets'] / out['totalLiabilities']
        out['debt_to_equity'] = ((out['shortTermDebt'].fillna(0)+out['longTermDebt'].fillna(0)) / out['totalStockholdersEquity'])
        out = out.replace([np.inf, -np.inf], np.nan)
        return out.reset_index()

    metrics_df = compute_metrics(income_df, balance_df, cashflow_df, metrics)

    # ----------------------
    # Executive Tab
    # ----------------------
    with tabs[0]:
        st.header("Executive Overview")
        st.write("High-level summary of cashflow, profitability and capital allocation. For a complete narrative upload income & balance data.")
        if metrics_df.empty:
            st.info("No prepared metrics available. Upload income, balance and cashflow files and press 'Validate & Prepare Data'.")
        else:
            cols = st.columns(4)
            latest = metrics_df.iloc[-1]
            cols[0].metric("Latest FCF (B)", fmt_b(latest['freeCashFlow'] / Decimal(1e9)))
            cols[1].metric("Latest OCF (B)", fmt_b(latest['operatingCashFlow'] / Decimal(1e9)))
            cols[2].metric("Latest Net Income (B)", fmt_b(latest['netIncome'] / Decimal(1e9)))
            cols[3].metric("Net Debt (B)", fmt_b(latest['netDebt'] / Decimal(1e9)))

            st.subheader('Trend — Revenue / Net Income / OCF / FCF')
            plot_df = metrics_df.set_index('fiscalYear')[['revenue','netIncome','operatingCashFlow','freeCashFlow']]
            st.line_chart(plot_df.apply(lambda x: x/Decimal(1e9)))

    # ----------------------
    # Profit Engine Tab
    # ----------------------
    with tabs[1]:
        st.header('Profit Engine')
        st.write('Revenue growth, margins and operating leverage.')
        if metrics_df.empty:
            st.info('Upload income statement to view profit engine.')
        else:
            # Margins
            print(metrics_df[["grossProfit", "operatingIncome", "netIncome"]])
            metrics_df['grossMargin'] = metrics_df['grossProfit'] / metrics_df['revenue']
            metrics_df['opMargin'] = metrics_df['operatingIncome'] / metrics_df['revenue']
            metrics_df['netMargin'] = metrics_df['netIncome'] / metrics_df['revenue']
            fig = go.Figure()
            fig.add_trace(go.Bar(x=metrics_df['fiscalYear'], y=metrics_df['grossMargin'], name='Gross Margin'))
            fig.add_trace(go.Bar(x=metrics_df['fiscalYear'], y=metrics_df['opMargin'], name='Operating Margin'))
            fig.add_trace(go.Bar(x=metrics_df['fiscalYear'], y=metrics_df['netMargin'], name='Net Margin'))
            fig.update_layout(barmode='group', yaxis_tickformat=',.0%', height=420)
            st.plotly_chart(fig, width='stretch')

            st.subheader('Revenue growth')
            metrics_df['rev_yoy'] = metrics_df['revenue'].pct_change()
            st.bar_chart(metrics_df.set_index('fiscalYear')['rev_yoy'].apply(lambda x: x*100))

    # ----------------------
    # Cash Engine Tab
    # ----------------------
    with tabs[2]:
        st.header('Cash Engine')
        st.write('Operating cash flow quality, working capital, and cash bridges.')
        if metrics_df.empty:
            st.info('Upload cashflow statement for cash engine analysis.')
        else:
            st.subheader('OCF / Net Income')
            st.line_chart(metrics_df.set_index('fiscalYear')['OCF_to_NetIncome'])

            st.subheader('FCF Bridge (OCF -> CapEx -> FCF)')
            # simple waterfall across years
            years = metrics_df['fiscalYear'].astype(str).tolist()

            wf = go.Figure()

            wf.add_trace(go.Bar(
                x=years,
                y=(metrics_df['operatingCashFlow'] / Decimal(1e9)),
                name='OCF'
            ))

            wf.add_trace(go.Bar(
                x=years,
                y=(metrics_df['capitalExpenditure'] / Decimal(1e9)),
                name='CapEx'
            ))

            wf.add_trace(go.Bar(
                x=years,
                y=(metrics_df['freeCashFlow'] / Decimal(1e9)),
                name='FCF'
            ))

            wf.update_layout(
                barmode='group',
                height=420,
                yaxis_title='Billions USD'
            )

            st.plotly_chart(wf, width='stretch')


            st.subheader('Working Capital (change)')
            if 'changeInWorkingCapital' in metrics_df.columns:
                st.bar_chart(metrics_df.set_index('fiscalYear')['changeInWorkingCapital'].apply(lambda x: x/1e9))

    # ----------------------
    # Investment Tab
    # ----------------------
    with tabs[3]:
        st.header('Investment Engine')
        st.write('CapEx, R&D (if available), and cash ROIC.')
        if metrics_df.empty:
            st.info('Upload data to analyze investment engine.')
        else:
            st.subheader('CapEx vs Revenue')
            st.line_chart(metrics_df.set_index('fiscalYear')[['capitalExpenditure','revenue']].apply(lambda x: x/1e9))
            st.subheader('CapEx / Revenue')
            st.line_chart(metrics_df.set_index('fiscalYear')['capex_to_revenue'])

    # ----------------------
    # Capital Allocation Tab
    # ----------------------
    with tabs[4]:
        st.header('Capital Allocation')
        st.write('Buybacks, dividends, debt activity and payout ratios')
        if metrics_df.empty:
            st.info('Upload cashflow and balance sheet to enable capital allocation analysis.')
        else:
            st.subheader('Buybacks & Dividends (B)')
            bd = metrics_df.set_index('fiscalYear')[['buybacks','dividends']].apply(lambda x: x/(1e9))
            st.bar_chart(bd)

            st.subheader('Payout ratio (Buybacks+Dividends) / FCF')
            st.line_chart(metrics_df.set_index('fiscalYear')['payout_pct_of_FCF'])

            st.subheader('Net Debt')
            st.line_chart(metrics_df.set_index('fiscalYear')['netDebt'].apply(lambda x: x/(1e9)))

    # ----------------------
    # Financial Strength Tab
    # ----------------------
    with tabs[5]:
        st.header('Financial Strength')
        st.write('Liquidity, leverage and coverage metrics')
        if metrics_df.empty:
            st.info('Upload balance sheet to compute leverage and liquidity ratios.')
        else:
            cols = st.columns(3)
            cols[0].metric('Latest Cash (B)', fmt_b(metrics_df.iloc[-1]['cashAndCashEquivalents']))
            cols[1].metric('Debt to Equity', f"{metrics_df.iloc[-1]['debt_to_equity']:.2f}")
            cols[2].metric('Current ratio', f"{metrics_df.iloc[-1]['current_ratio']:.2f}")

    # ----------------------
    # Valuation Tab
    # ----------------------
    with tabs[6]:
        st.header('Valuation')
        st.write('DCF (scenario) and relative valuation based on FCF if market data provided.')
        if metrics_df.empty:
            st.info('Upload statements and provide market data (market cap/price/shares) for valuation.')
        else:
            last_fcf = metrics_df.iloc[-1]['freeCashFlow']
            st.write(f"Last reported FCF: **{fmt_b(last_fcf)}**")
            # DCF inputs
            r = st.number_input('Discount rate (WACC %)', value=8.0)
            growth = st.number_input('Base FCF growth % p.a.', value=3.0)
            years = st.slider('Forecast years', min_value=3, max_value=20, value=5)
            term_g = st.number_input('Terminal growth %', value=2.0)
            shares = st.number_input('Shares outstanding (in billions)', value=15.8)

            # compute
            fcf0 = last_fcf
            g = growth/100.0
            rdec = r/100.0
            fcf_proj = [fcf0 * Decimal((1+g)**i) for i in range(1, years+1)]
            pv = [fcf_proj[i]/(Decimal(1+rdec)**Decimal(i+1)) for i in range(len(fcf_proj))]
            tv = fcf_proj[-1]*Decimal(1+term_g/100.0)/Decimal(rdec-term_g/100.0) if rdec>term_g/100.0 else np.nan
            pv_tv = tv/Decimal((1+rdec)**years) if not None else np.nan
            npv = sum(pv) + (pv_tv if pv_tv is not None else 0)
            per_share = npv / Decimal(shares*1e9) if shares>0 else np.nan

            st.metric('Intrinsic NPV (FCF discounted, USD B)', fmt_b(npv))
            st.metric('Implied per-share (USD)', f"${per_share:,.2f}" if not None else 'n/a')

    # ----------------------
    # Narrative Generator Tab
    # ----------------------
    with tabs[7]:
        st.header('Narrative Generator')
        st.write('Auto-generated narrative from computed metrics. Edit or export the narrative as text.')
        if metrics_df.empty:
            st.info('Upload data to generate a narrative.')
        else:
            latest = metrics_df.iloc[-1]
            # Build narrative components
            lines = []
            lines.append(f"Executive summary — Fiscal Year {int(latest['fiscalYear'])}:")
            lines.append(f"Apple generated {fmt_b(latest['freeCashFlow'])} of free cash flow in the latest fiscal year, with operating cash flow of {fmt_b(latest['operatingCashFlow'])} and net income of {fmt_b(latest['netIncome'])}.")
            ocf_ratio = latest['OCF_to_NetIncome']
            if ocf_ratio is not None:
                lines.append(f"Cash conversion (OCF / Net Income) was {ocf_ratio:.2f}x, indicating {'strong' if ocf_ratio>1.0 else 'weaker'} earnings quality.")
            if 'payout_pct_of_FCF' in latest and latest['payout_pct_of_FCF'] is not None:
                lines.append(f"Management returned {latest['payout_pct_of_FCF']*100:.1f}% of FCF to shareholders via buybacks and dividends in the year.")
            if 'netDebt' in latest and latest['netDebt'] is not None:
                lines.append(f"Net debt stands at {fmt_b(latest['netDebt'])}.")

            # Working capital narrative
            if 'changeInWorkingCapital' in latest and latest['changeInWorkingCapital'] is not None:
                delta_wc = latest['changeInWorkingCapital']
                if delta_wc < 0:
                    lines.append(f"Working capital change was a headwind to cash flow of {fmt_b(delta_wc)} (cash outflow).")
                else:
                    lines.append(f"Working capital supported cash flow by {fmt_b(delta_wc)} (cash inflow).")

            # Investment narrative
            if 'capitalExpenditure' in latest and latest['capitalExpenditure'] is not None:
                lines.append(f"Capital expenditure was {fmt_b(latest['capitalExpenditure'])}, representing {latest['capex_to_revenue']*100:.2f}% of revenue (if revenue data provided)." )

            # Risk / forward view
            lines.append('Key risks include sustained increases in working capital requirements, larger-than-expected capex, or slowing revenue growth which would reduce FCF. Upside comes from margin expansion or services growth.')

            narrative = ''.join(lines)
            narrative = st.text_area('Auto-generated narrative (editable)', value=narrative, height=300)
            st.download_button('Download narrative', data=narrative, file_name='aapl_narrative.txt', mime='text/plain')

    # ----------------------
    # Data Tab
    # ----------------------
    with tabs[8]:
        st.header('Data & Tables')
        st.write('Inspect uploaded data and prepared metrics. You can download the merged metrics as CSV for offline use.')
        st.subheader('Prepared metrics')
        st.dataframe(metrics_df)
        if not metrics_df.empty:
            csv = metrics_df.to_csv(index=False)
            st.download_button('Download metrics CSV', data=csv, file_name='metrics.csv', mime='text/csv')

    st.markdown('---')
    st.caption('Disclaimer: this app is a tool for an explanatory narrative and visualization engine, not an investment advisor.')
