"""Offline tests for the valuation engine (no network required).

    python -m pytest -q
"""
import pytest

from valuation.assumptions import Assumptions
from valuation.data import CompanySnapshot
from valuation.dcf import run_dcf, scenarios, _run_dcf_with_wacc
from valuation.report import recommend


def make_snap():
    return CompanySnapshot(
        ticker="TEST", name="Test Co", price=1000.0, shares=1e8,
        revenue=10000.0, ebit=1100.0, ebitda=1400.0, da=300.0,
        total_debt=500.0, cash=200.0, tax_rate=0.25, beta=1.0,
    )


def test_dcf_runs_and_is_positive():
    snap, a = make_snap(), Assumptions()
    res = run_dcf(snap, a)
    assert res.fair_value_gordon > 0
    assert res.enterprise_value > res.equity_value  # net debt is positive here


def test_wacc_above_growth_required():
    snap = make_snap()
    bad = Assumptions(terminal_growth=0.50)  # exceeds any sane WACC
    with pytest.raises(ValueError):
        run_dcf(snap, bad)


def test_higher_wacc_lowers_value():
    snap, a = make_snap(), Assumptions()
    low = _run_dcf_with_wacc(snap, a, 0.10)
    high = _run_dcf_with_wacc(snap, a, 0.14)
    assert high < low


def test_higher_terminal_growth_raises_value():
    snap = make_snap()
    a_low = Assumptions(terminal_growth=0.04)
    a_high = Assumptions(terminal_growth=0.07)
    assert run_dcf(snap, a_high).fair_value_gordon > run_dcf(snap, a_low).fair_value_gordon


def test_scenarios_ordered():
    snap, a = make_snap(), Assumptions()
    sc = scenarios(snap, a)
    assert sc["bear"] < sc["base"] < sc["bull"]


def test_projection_length_and_growth():
    snap, a = make_snap(), Assumptions()
    proj = run_dcf(snap, a).projections
    assert len(proj) == a.years
    # revenue compounds upward
    assert proj["revenue"].is_monotonic_increasing


@pytest.mark.parametrize("upside,expected", [(0.30, "BUY"), (0.05, "HOLD"), (-0.25, "SELL")])
def test_recommendation_bands(upside, expected):
    assert recommend(upside) == expected


def test_net_debt_and_ev():
    snap = make_snap()
    assert snap.net_debt == pytest.approx(300.0)         # 500 - 200
    # 1e8 shares = 10 crore shares; at INR 1000 -> 10,000 cr market cap
    assert snap.market_cap == pytest.approx(10000.0)     # 1000 * 1e8 / 1e7
    assert snap.enterprise_value == pytest.approx(10300.0)  # mktcap + net debt
