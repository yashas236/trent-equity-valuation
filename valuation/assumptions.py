"""Valuation assumptions for the DCF and comps models.

Every input a recruiter or reviewer might question lives here, with a short
justification. Trent Ltd (NSE: TRENT) is a Tata-group retailer (Westside,
Zudio) that has compounded revenue at 30-40% recently while trading at very rich
multiples (trailing P/E ~90x, EV/EBITDA ~50x). The defaults below assume a fast
but *fading* growth path toward a mature retailer profile.

All monetary figures are in INR crore (1 crore = 1e7).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Assumptions:
    # --- explicit-forecast horizon -----------------------------------------
    years: int = 5

    # Revenue growth path over the explicit window (fades from hyper-growth to
    # a mature rate). Trent grew ~19% in the trailing year per the latest data;
    # we taper toward the terminal rate.
    revenue_growth: List[float] = field(
        default_factory=lambda: [0.30, 0.25, 0.20, 0.16, 0.12]
    )

    # EBIT margin path. Latest operating margin ~11%; we allow modest operating
    # leverage as the store base matures.
    ebit_margin: List[float] = field(
        default_factory=lambda: [0.115, 0.118, 0.120, 0.122, 0.124]
    )

    tax_rate: float = 0.25            # Indian corporate tax (new regime)
    da_pct_revenue: float = 0.030     # depreciation & amortization as % of sales
    capex_pct_revenue: float = 0.040  # store expansion capex as % of sales
    nwc_pct_delta_revenue: float = 0.05  # incremental net working capital per ₹ of new sales

    # --- WACC (CAPM cost of equity + after-tax cost of debt) ----------------
    risk_free: float = 0.070          # ~Indian 10Y G-sec
    equity_risk_premium: float = 0.060
    beta: float = 0.95                # sensible retail beta (yfinance's 0.35 is
                                      # implausibly low; see README note)
    cost_of_debt: float = 0.085       # pre-tax
    # Target capital structure (Trent is largely equity-financed; lease debt aside)
    weight_equity: float = 0.92
    weight_debt: float = 0.08

    # --- terminal value -----------------------------------------------------
    terminal_growth: float = 0.06     # ~ long-run nominal GDP / mature retail
    exit_ev_ebitda: float = 22.0      # cross-check terminal multiple (premium retailer)

    # --- scenario shifts (applied to revenue growth & margins) --------------
    bull_growth_uplift: float = 0.04
    bear_growth_haircut: float = 0.05

    def cost_of_equity(self) -> float:
        return self.risk_free + self.beta * self.equity_risk_premium

    def wacc(self) -> float:
        ke = self.cost_of_equity()
        kd = self.cost_of_debt * (1 - self.tax_rate)
        return self.weight_equity * ke + self.weight_debt * kd


# Defaults instance used by the example runner.
TRENT_DEFAULTS = Assumptions()
