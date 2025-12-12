from typing import Optional
from typing import List
from pydantic import BaseModel, validator
from decimal import Decimal

class Ratios(BaseModel):
    symbol: str
    date: str
    fiscalYear: int
    period: str
    reportedCurrency: str
    grossProfitMargin: Decimal
    ebitMargin: Decimal
    ebitdaMargin: Decimal
    operatingProfitMargin: Decimal
    pretaxProfitMargin: Decimal
    continuousOperationsProfitMargin: Decimal
    netProfitMargin: Decimal
    bottomLineProfitMargin: Decimal
    receivablesTurnover: Decimal
    payablesTurnover: Decimal
    inventoryTurnover: Decimal
    fixedAssetTurnover: Decimal
    assetTurnover: Decimal
    currentRatio: Decimal
    quickRatio: Decimal
    solvencyRatio: Decimal
    cashRatio: Decimal
    priceToEarningsRatio: Decimal
    priceToEarningsGrowthRatio: Decimal
    forwardPriceToEarningsGrowthRatio: Decimal
    priceToBookRatio: Decimal
    priceToSalesRatio: Decimal
    priceToFreeCashFlowRatio: Decimal
    priceToOperatingCashFlowRatio: Decimal
    debtToAssetsRatio: Decimal
    debtToEquityRatio: Decimal
    debtToCapitalRatio: Decimal
    longTermDebtToCapitalRatio: Decimal
    financialLeverageRatio: Decimal
    workingCapitalTurnoverRatio: Decimal
    operatingCashFlowRatio: Decimal
    operatingCashFlowSalesRatio: Decimal
    freeCashFlowOperatingCashFlowRatio: Decimal
    debtServiceCoverageRatio: Decimal
    interestCoverageRatio: Decimal
    shortTermOperatingCashFlowCoverageRatio: Decimal
    operatingCashFlowCoverageRatio: Decimal
    capitalExpenditureCoverageRatio: Decimal
    dividendPaidAndCapexCoverageRatio: Decimal
    dividendPayoutRatio: Decimal
    dividendYield: Decimal
    dividendYieldPercentage: Decimal
    revenuePerShare: Decimal
    netIncomePerShare: Decimal
    interestDebtPerShare: Decimal
    cashPerShare: Decimal
    bookValuePerShare: Decimal
    tangibleBookValuePerShare: Decimal
    shareholdersEquityPerShare: Decimal
    operatingCashFlowPerShare: Decimal
    capexPerShare: Decimal
    freeCashFlowPerShare: Decimal
    netIncomePerEBT: Decimal
    ebtPerEbit: Decimal
    priceToFairValue: Decimal
    debtToMarketCap: Decimal
    effectiveTaxRate: Decimal
    enterpriseValueMultiple: Decimal
    dividendPerShare: Decimal

class KeyMetrics(BaseModel):
    """
    Flexible Pydantic model for FMP Key Metrics response.
    FMP adds new fields often, so we allow extra fields.
    """
    symbol: str
    date: str
    fiscalYear: Optional[str]
    period: Optional[str]
    reportedCurrency: Optional[str]
    marketCap: Decimal
    enterpriseValue: Decimal
    evToSales: Decimal
    evToOperatingCashFlow: Decimal
    evToFreeCashFlow: Decimal
    evToEBITDA: Decimal
    netDebtToEBITDA: Decimal
    currentRatio: Decimal
    incomeQuality: Decimal
    grahamNumber: Optional[Decimal]
    grahamNetNet: Decimal
    taxBurden: Decimal
    interestBurden: Decimal
    workingCapital: Decimal
    investedCapital: Decimal
    returnOnAssets: Decimal
    operatingReturnOnAssets: Decimal
    returnOnTangibleAssets: Decimal
    returnOnEquity: Decimal
    returnOnInvestedCapital: Decimal
    returnOnCapitalEmployed: Decimal
    earningsYield: Decimal
    freeCashFlowYield: Decimal
    capexToOperatingCashFlow: Decimal
    capexToDepreciation: Decimal
    capexToRevenue: Decimal
    salesGeneralAndAdministrativeToRevenue: Decimal
    researchAndDevelopementToRevenue: Decimal
    stockBasedCompensationToRevenue: Decimal
    intangiblesToTotalAssets: Decimal
    averageReceivables: Decimal
    averagePayables: Decimal
    averageInventory: Decimal
    daysOfSalesOutstanding: Decimal
    daysOfPayablesOutstanding: Decimal
    daysOfInventoryOutstanding: Decimal
    operatingCycle: Decimal
    cashConversionCycle: Decimal
    freeCashFlowToEquity: Decimal
    freeCashFlowToFirm: Decimal
    tangibleAssetValue: Decimal
    netCurrentAssetValue: Decimal
     
    def float_to_decimal(cls, v):
        if isinstance(v, Decimal):
            return Decimal(str(v))
        return v


class BalanceSheet(BaseModel):
    date: str
    symbol: str
    reportedCurrency: str
    cik: str
    filingDate: str
    acceptedDate: str
    fiscalYear: str
    period: str

    cashAndCashEquivalents: Decimal
    shortTermInvestments: Decimal
    cashAndShortTermInvestments: Decimal
    netReceivables: Decimal
    accountsReceivables: Decimal
    otherReceivables: Decimal
    inventory: Decimal
    prepaids: Decimal
    otherCurrentAssets: Decimal
    totalCurrentAssets: Decimal

    propertyPlantEquipmentNet: Decimal
    goodwill: Decimal
    intangibleAssets: Decimal
    goodwillAndIntangibleAssets: Decimal
    longTermInvestments: Decimal
    taxAssets: Decimal
    otherNonCurrentAssets: Decimal
    totalNonCurrentAssets: Decimal
    otherAssets: Decimal
    totalAssets: Decimal

    totalPayables: Decimal
    accountPayables: Decimal
    otherPayables: Decimal
    accruedExpenses: Decimal
    shortTermDebt: Decimal
    capitalLeaseObligationsCurrent: Decimal
    taxPayables: Decimal
    deferredRevenue: Decimal
    otherCurrentLiabilities: Decimal
    totalCurrentLiabilities: Decimal

    longTermDebt: Decimal
    deferredRevenueNonCurrent: Decimal
    deferredTaxLiabilitiesNonCurrent: Decimal
    otherNonCurrentLiabilities: Decimal
    totalNonCurrentLiabilities: Decimal
    otherLiabilities: Decimal
    capitalLeaseObligations: Decimal
    totalLiabilities: Decimal

    treasuryStock: Decimal
    preferredStock: Decimal
    commonStock: Decimal
    retainedEarnings: Decimal
    additionalPaidInCapital: Decimal
    accumulatedOtherComprehensiveIncomeLoss: Decimal
    otherTotalStockholdersEquity: Decimal
    totalStockholdersEquity: Decimal
    totalEquity: Decimal
    minorityInterest: Decimal
    totalLiabilitiesAndTotalEquity: Decimal

    totalInvestments: Decimal
    totalDebt: Decimal
    netDebt: Decimal

    def float_to_decimal(cls, v):
        if isinstance(v, Decimal):
            return Decimal(str(v))
        return v

class IncomeStatement(BaseModel):
    date: str
    symbol: str
    reportedCurrency: str
    cik: str
    filingDate: str
    acceptedDate: str
    fiscalYear: str
    period: str

    revenue: Decimal
    costOfRevenue: Decimal
    grossProfit: Decimal

    researchAndDevelopmentExpenses: Decimal
    generalAndAdministrativeExpenses: Decimal
    sellingAndMarketingExpenses: Decimal
    sellingGeneralAndAdministrativeExpenses: Decimal
    otherExpenses: Decimal
    operatingExpenses: Decimal
    costAndExpenses: Decimal

    netInterestIncome: Decimal
    interestIncome: Decimal
    interestExpense: Decimal

    depreciationAndAmortization: Decimal
    ebitda: Decimal
    ebit: Decimal

    nonOperatingIncomeExcludingInterest: Decimal
    operatingIncome: Decimal
    totalOtherIncomeExpensesNet: Decimal
    incomeBeforeTax: Decimal
    incomeTaxExpense: Decimal
    netIncomeFromContinuingOperations: Decimal
    netIncomeFromDiscontinuedOperations: Decimal
    otherAdjustmentsToNetIncome: Decimal
    netIncome: Decimal
    netIncomeDeductions: Decimal
    bottomLineNetIncome: Decimal

    eps: Decimal
    epsDiluted: Decimal
    weightedAverageShsOut: Decimal
    weightedAverageShsOutDil: Decimal

    def float_to_decimal(cls, v):
        if isinstance(v, Decimal):
            return Decimal(str(v))
        return v

# For a list of objects
IncomeStatementList = List[IncomeStatement]


class CashFlowStatement(BaseModel):
    date: str
    symbol: str
    reportedCurrency: str
    cik: str
    filingDate: str
    acceptedDate: str
    fiscalYear: str
    period: str

    netIncome: Decimal
    depreciationAndAmortization: Decimal
    deferredIncomeTax: Decimal
    stockBasedCompensation: Decimal
    changeInWorkingCapital: Decimal

    accountsReceivables: Decimal
    inventory: Decimal
    accountsPayables: Decimal
    otherWorkingCapital: Decimal
    otherNonCashItems: Decimal

    netCashProvidedByOperatingActivities: Decimal

    investmentsInPropertyPlantAndEquipment: Decimal
    acquisitionsNet: Decimal
    purchasesOfInvestments: Decimal
    salesMaturitiesOfInvestments: Decimal
    otherInvestingActivities: Decimal
    netCashProvidedByInvestingActivities: Decimal

    netDebtIssuance: Decimal
    longTermNetDebtIssuance: Decimal
    shortTermNetDebtIssuance: Decimal

    netStockIssuance: Decimal
    netCommonStockIssuance: Decimal
    commonStockIssuance: Decimal
    commonStockRepurchased: Decimal
    netPreferredStockIssuance: Decimal

    netDividendsPaid: Decimal
    commonDividendsPaid: Decimal
    preferredDividendsPaid: Decimal
    otherFinancingActivities: Decimal
    netCashProvidedByFinancingActivities: Decimal

    effectOfForexChangesOnCash: Decimal
    netChangeInCash: Decimal

    cashAtEndOfPeriod: Decimal
    cashAtBeginningOfPeriod: Decimal

    operatingCashFlow: Decimal
    capitalExpenditure: Decimal
    freeCashFlow: Decimal

    incomeTaxesPaid: Decimal
    interestPaid: Decimal

    def float_to_decimal(cls, v):
        if isinstance(v, Decimal):
            return Decimal(str(v))
        return v
# For a list of entries
CashFlowStatementList = List[CashFlowStatement]
