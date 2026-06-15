"""Discounted-cash-flow valuation (unlevered FCFF -> enterprise -> equity).

FCFF_t = EBIT_t (1 - tax) + D&A_t - Capex_t - Delta_NWC_t

Enterprise value = sum of discounted FCFF over the explicit horizon plus the
discounted terminal value. We compute the terminal value two ways — Gordon
growth and an exit EV/EBITDA multiple — and report both. Equity value per share
= (EV - net debt) / shares outstanding.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .assumptions import Assumptions
from .data import CompanySnapshot


@dataclass
class DCFResult:
    projections: pd.DataFrame
    wacc: float
    pv_explicit: float          # INR crore
    terminal_value_gordon: float
    pv_terminal_gordon: float
    enterprise_value: float     # Gordon-based
    equity_value: float
    fair_value_gordon: float    # INR/share
    fair_value_exit: float      # INR/share, exit-multiple terminal
    upside_gordon: float        # vs market price


def _project(snap: CompanySnapshot, a: Assumptions, growth_path) -> pd.DataFrame:
    rev_prev = snap.revenue
    rows = []
    for i in range(a.years):
        g = growth_path[i]
        rev = rev_prev * (1 + g)
        ebit = rev * a.ebit_margin[i]
        nopat = ebit * (1 - a.tax_rate)
        da = rev * a.da_pct_revenue
        capex = rev * a.capex_pct_revenue
        d_nwc = (rev - rev_prev) * a.nwc_pct_delta_revenue
        fcff = nopat + da - capex - d_nwc
        ebitda = ebit + da
        rows.append(
            dict(year=i + 1, revenue=rev, growth=g, ebit=ebit, ebit_margin=a.ebit_margin[i],
                 nopat=nopat, da=da, capex=capex, d_nwc=d_nwc, fcff=fcff, ebitda=ebitda)
        )
        rev_prev = rev
    return pd.DataFrame(rows)


def run_dcf(snap: CompanySnapshot, a: Assumptions, growth_path=None) -> DCFResult:
    growth_path = list(a.revenue_growth if growth_path is None else growth_path)
    wacc = a.wacc()
    proj = _project(snap, a, growth_path)

    disc = (1 + wacc) ** proj["year"].values
    proj["discount_factor"] = 1 / disc
    proj["pv_fcff"] = proj["fcff"].values * proj["discount_factor"].values
    pv_explicit = float(proj["pv_fcff"].sum())

    last_fcff = float(proj["fcff"].iloc[-1])
    last_ebitda = float(proj["ebitda"].iloc[-1])
    g = a.terminal_growth

    # Gordon-growth terminal value
    if wacc <= g:
        raise ValueError("WACC must exceed terminal growth for the Gordon model")
    tv_gordon = last_fcff * (1 + g) / (wacc - g)
    pv_tv_gordon = tv_gordon / (1 + wacc) ** a.years

    # Exit-multiple terminal value (cross-check)
    tv_exit = a.exit_ev_ebitda * last_ebitda
    pv_tv_exit = tv_exit / (1 + wacc) ** a.years

    ev_gordon = pv_explicit + pv_tv_gordon
    ev_exit = pv_explicit + pv_tv_exit

    equity_gordon = ev_gordon - snap.net_debt
    equity_exit = ev_exit - snap.net_debt
    shares_cr = snap.shares / 1e7  # crore of shares (since values are in INR crore)

    fair_gordon = equity_gordon / shares_cr
    fair_exit = equity_exit / shares_cr

    return DCFResult(
        projections=proj,
        wacc=wacc,
        pv_explicit=pv_explicit,
        terminal_value_gordon=tv_gordon,
        pv_terminal_gordon=pv_tv_gordon,
        enterprise_value=ev_gordon,
        equity_value=equity_gordon,
        fair_value_gordon=fair_gordon,
        fair_value_exit=fair_exit,
        upside_gordon=fair_gordon / snap.price - 1,
    )


def scenarios(snap: CompanySnapshot, a: Assumptions) -> dict:
    """Bull / base / bear fair values by shifting the growth path."""
    base = list(a.revenue_growth)
    bull = [g + a.bull_growth_uplift for g in base]
    bear = [max(g - a.bear_growth_haircut, 0.0) for g in base]
    return {
        "bear": run_dcf(snap, a, bear).fair_value_gordon,
        "base": run_dcf(snap, a, base).fair_value_gordon,
        "bull": run_dcf(snap, a, bull).fair_value_gordon,
    }


def sensitivity(snap: CompanySnapshot, a: Assumptions, wacc_range=None, g_range=None) -> pd.DataFrame:
    """Per-share fair value across a WACC x terminal-growth grid."""
    base_wacc = a.wacc()
    wacc_range = wacc_range if wacc_range is not None else np.round(
        np.linspace(base_wacc - 0.02, base_wacc + 0.02, 5), 4
    )
    g_range = g_range if g_range is not None else np.round(
        np.linspace(a.terminal_growth - 0.02, a.terminal_growth + 0.02, 5), 4
    )
    grid = pd.DataFrame(index=[f"{w:.1%}" for w in wacc_range], columns=[f"{g:.1%}" for g in g_range], dtype=float)
    for w in wacc_range:
        for g in g_range:
            aa = Assumptions(**{**a.__dict__})
            # override the computed WACC by adjusting via a thin wrapper:
            aa_wacc = w
            aa.terminal_growth = float(g)
            # build a result using an explicit wacc override
            res = _run_dcf_with_wacc(snap, aa, aa_wacc)
            grid.loc[f"{w:.1%}", f"{g:.1%}"] = round(res, 1)
    grid.index.name = "WACC \\ g"
    return grid


def _run_dcf_with_wacc(snap: CompanySnapshot, a: Assumptions, wacc: float) -> float:
    """DCF fair value (Gordon) with an externally supplied WACC."""
    proj = _project(snap, a, list(a.revenue_growth))
    years = np.arange(1, a.years + 1)
    pv_explicit = float((proj["fcff"].values / (1 + wacc) ** years).sum())
    last_fcff = float(proj["fcff"].iloc[-1])
    g = a.terminal_growth
    if wacc <= g:
        return float("nan")
    tv = last_fcff * (1 + g) / (wacc - g)
    pv_tv = tv / (1 + wacc) ** a.years
    equity = (pv_explicit + pv_tv) - snap.net_debt
    return equity / (snap.shares / 1e7)
