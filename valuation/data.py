"""Pull a company snapshot from Yahoo Finance, with documented fallbacks.

Indian fundamentals on Yahoo can have gaps, so every field has a fallback and
the snapshot records which values were defaulted. All monetary values are
converted to INR crore (1 crore = 1e7).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import List

warnings.filterwarnings("ignore")

CRORE = 1e7


@dataclass
class CompanySnapshot:
    ticker: str
    name: str
    price: float                 # INR per share
    shares: float                # absolute count
    revenue: float               # INR crore, latest FY
    ebit: float                  # INR crore
    ebitda: float                # INR crore
    da: float                    # INR crore (depreciation & amortization)
    total_debt: float            # INR crore
    cash: float                  # INR crore
    tax_rate: float
    beta: float
    revenue_history: List[float] = field(default_factory=list)  # INR crore, oldest->newest
    defaulted: List[str] = field(default_factory=list)

    @property
    def net_debt(self) -> float:
        return self.total_debt - self.cash

    @property
    def market_cap(self) -> float:
        return self.price * self.shares / CRORE

    @property
    def enterprise_value(self) -> float:
        return self.market_cap + self.net_debt


def _get(info, key, default, snap_defaults, label):
    val = info.get(key)
    if val is None or (isinstance(val, float) and val != val):  # None or NaN
        snap_defaults.append(label)
        return default
    return val


def fetch_snapshot(ticker: str) -> CompanySnapshot:
    import yfinance as yf

    t = yf.Ticker(ticker)
    info = t.info
    defaulted: List[str] = []

    price = _get(info, "currentPrice", info.get("previousClose", 0.0), defaulted, "price")
    shares = _get(info, "sharesOutstanding", 0.0, defaulted, "shares")
    revenue = _get(info, "totalRevenue", 0.0, defaulted, "revenue") / CRORE
    ebitda = _get(info, "ebitda", 0.0, defaulted, "ebitda") / CRORE
    op_margin = _get(info, "operatingMargins", 0.11, defaulted, "operatingMargins")
    total_debt = _get(info, "totalDebt", 0.0, defaulted, "total_debt") / CRORE
    cash = _get(info, "totalCash", 0.0, defaulted, "cash") / CRORE
    beta = _get(info, "beta", 0.95, defaulted, "beta")

    ebit = revenue * op_margin
    da = max(ebitda - ebit, 0.0)

    # historical revenue from the income statement (oldest -> newest)
    rev_hist: List[float] = []
    try:
        fin = t.financials
        if fin is not None and "Total Revenue" in fin.index:
            rev_hist = [float(x) / CRORE for x in fin.loc["Total Revenue"][::-1] if x == x]
    except Exception:
        pass

    return CompanySnapshot(
        ticker=ticker,
        name=info.get("shortName", ticker),
        price=float(price),
        shares=float(shares),
        revenue=float(revenue),
        ebit=float(ebit),
        ebitda=float(ebitda),
        da=float(da),
        total_debt=float(total_debt),
        cash=float(cash),
        tax_rate=0.25,
        beta=float(beta),
        revenue_history=rev_hist,
        defaulted=defaulted,
    )


def fetch_peer_multiples(tickers: List[str]):
    """Return a DataFrame of EV/EBITDA and trailing P/E for each peer."""
    import pandas as pd
    import yfinance as yf

    rows = []
    for sym in tickers:
        try:
            info = yf.Ticker(sym).info
            rows.append(
                {
                    "ticker": sym,
                    "name": info.get("shortName", sym),
                    "ev_ebitda": info.get("enterpriseToEbitda"),
                    "pe": info.get("trailingPE"),
                    "rev_growth": info.get("revenueGrowth"),
                    "ebitda_margin": info.get("ebitdaMargins"),
                }
            )
        except Exception:
            rows.append({"ticker": sym, "name": sym, "ev_ebitda": None, "pe": None})
    return pd.DataFrame(rows)
