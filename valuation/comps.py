"""Trading-comparables valuation (relative value vs listed peers).

We apply the peer-group *median* EV/EBITDA and P/E multiples to Trent's own
EBITDA and earnings to derive an implied per-share value. The median is used
(not the mean) so a single richly-valued peer does not distort the benchmark.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from .data import CompanySnapshot, fetch_peer_multiples

# Listed Indian retail / branded-consumer peers.
DEFAULT_PEERS = [
    "DMART.NS",        # Avenue Supermarts
    "ABFRL.NS",        # Aditya Birla Fashion & Retail
    "SHOPERSTOP.NS",   # Shoppers Stop
    "VMART.NS",        # V-Mart Retail
    "MANYAVAR.NS",     # Vedant Fashions
    "PAGEIND.NS",      # Page Industries
    "BATAINDIA.NS",    # Bata India
]


@dataclass
class CompsResult:
    peer_table: pd.DataFrame
    median_ev_ebitda: float
    median_pe: float
    trent_ev_ebitda: float
    trent_pe: float
    implied_value_ev_ebitda: float   # INR/share
    implied_value_pe: float          # INR/share
    blended_value: float             # INR/share
    upside: float                    # blended vs market price


def _clean_median(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    s = s[(s > 0) & (s < 500)]  # drop nonsensical / negative multiples
    return float(s.median()) if len(s) else float("nan")


def run_comps(snap: CompanySnapshot, peers: List[str] = None) -> CompsResult:
    import yfinance as yf

    peers = peers or DEFAULT_PEERS
    table = fetch_peer_multiples(peers)

    median_ev_ebitda = _clean_median(table["ev_ebitda"])
    median_pe = _clean_median(table["pe"])

    # Trent's own multiples for context
    info = yf.Ticker(snap.ticker).info
    trent_ev_ebitda = info.get("enterpriseToEbitda") or (snap.enterprise_value / snap.ebitda)
    trent_pe = info.get("trailingPE") or float("nan")
    trent_eps = info.get("trailingEps")
    if not trent_eps:  # fall back to a rough net income estimate
        net_income = snap.ebit * (1 - snap.tax_rate)
        trent_eps = net_income * 1e7 / snap.shares

    shares_cr = snap.shares / 1e7

    # EV/EBITDA -> implied equity per share
    implied_ev = median_ev_ebitda * snap.ebitda
    implied_equity = implied_ev - snap.net_debt
    implied_ev_ebitda_ps = implied_equity / shares_cr

    # P/E -> implied price per share
    implied_pe_ps = median_pe * trent_eps

    candidates = [v for v in (implied_ev_ebitda_ps, implied_pe_ps) if v == v]
    blended = float(np.mean(candidates)) if candidates else float("nan")

    return CompsResult(
        peer_table=table,
        median_ev_ebitda=median_ev_ebitda,
        median_pe=median_pe,
        trent_ev_ebitda=float(trent_ev_ebitda),
        trent_pe=float(trent_pe),
        implied_value_ev_ebitda=implied_ev_ebitda_ps,
        implied_value_pe=implied_pe_ps,
        blended_value=blended,
        upside=blended / snap.price - 1,
    )
