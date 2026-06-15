"""End-to-end Trent Ltd valuation.

    python -m examples.run_valuation

Pulls live data from Yahoo Finance; if that fails it falls back to a baked
snapshot (captured 2026-06-15) so the model always runs. Writes a football-field
chart, a sensitivity heatmap, and an Excel model to outputs/.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
OUT = os.path.join(_ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

from valuation import TRENT_DEFAULTS, fetch_snapshot
from valuation.data import CompanySnapshot
from valuation.report import build_report, print_summary, football_field, sensitivity_heatmap, export_excel

# Offline fallback (Yahoo Finance snapshot, 2026-06-15), values in INR crore.
SAMPLE_TRENT = CompanySnapshot(
    ticker="TRENT.NS", name="TRENT LTD", price=2901.1, shares=533_232_301,
    revenue=20074.2, ebit=2231.4, ebitda=2765.8, da=534.4,
    total_debt=2561.3, cash=928.9, tax_rate=0.25, beta=0.95,
    revenue_history=[8607.0, 11061.0, 12375.0, 16838.0, 20074.0],
    defaulted=["offline-fallback"],
)


def main():
    try:
        snap = fetch_snapshot("TRENT.NS")
        if snap.price <= 0 or snap.revenue <= 0:
            raise ValueError("incomplete live data")
        print("Using live Yahoo Finance data.\n")
    except Exception as e:
        print(f"[!] Live fetch failed ({type(e).__name__}); using baked 2026-06-15 snapshot.\n")
        snap = SAMPLE_TRENT

    rep = build_report(snap, TRENT_DEFAULTS)
    print_summary(rep)

    ff = football_field(rep, OUT)
    hm = sensitivity_heatmap(rep, OUT)
    xl = export_excel(rep, OUT)
    for p in (ff, hm, xl):
        print("wrote", os.path.relpath(p, _ROOT))


if __name__ == "__main__":
    main()
