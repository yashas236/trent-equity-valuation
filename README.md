# Trent Ltd — Equity Valuation Model (DCF + Comps)

A transparent, reproducible equity-valuation model for **Trent Ltd (NSE: TRENT)**,
the Tata-group retailer behind *Westside* and *Zudio*. It combines a
**discounted-cash-flow (DCF)** model with a **trading-comparables (comps)**
analysis, blends them into a single fair value, and issues a Buy / Hold / Sell
call. Live fundamentals are pulled from Yahoo Finance; every assumption is
explicit and editable in one file.

> **Not investment advice.** This is a modelling exercise. Outputs are entirely
> driven by the assumptions in [`valuation/assumptions.py`](valuation/assumptions.py)
> and reflect data as of the run date.

---

## Headline result

Representative run (live data, 2026-06-15):

| Method | Fair value (INR/share) |
|---|---|
| DCF — Gordon growth terminal | ~863 |
| DCF — exit-multiple terminal (22x) | ~1,968 |
| Comps — EV/EBITDA (peer median) | ~779 |
| Comps — P/E (peer median) | ~2,012 |
| **Blended fair value** | **~1,076** |
| Market price | 2,901 |
| **Implied downside / rating** | **~ -63% → SELL** |

Across **all four** methods Trent screens as richly valued: it trades at a
trailing **P/E ~90x** and **EV/EBITDA ~54x** versus peer medians near **15-60x**.
The thesis — *valuations are stretched, growth is more than priced in* — is robust
to the choice of terminal method. The bull case rests entirely on Trent
sustaining hyper-growth (Zudio) for far longer than a standard fade assumes; the
sensitivity table quantifies how much that matters.

*(Exact figures move with live data and assumptions; the script prints the
numbers for your run.)*

---

## Methodology

**DCF (unlevered free cash flow):**
```
FCFF_t = EBIT_t · (1 − tax) + D&A_t − Capex_t − ΔNWC_t
EV     = Σ FCFF_t / (1+WACC)^t  +  PV(terminal value)
Equity = EV − net debt          Fair value = Equity / shares
```
- 5-year explicit forecast with a **fading** revenue-growth path.
- **WACC** from CAPM cost of equity + after-tax cost of debt.
- Terminal value computed **two ways** — Gordon growth *and* an exit EV/EBITDA
  multiple — as a cross-check.
- A **WACC × terminal-growth sensitivity grid** and **bull/base/bear** scenarios.

**Comps (relative value):** peer-group **median** EV/EBITDA and P/E applied to
Trent's EBITDA and EPS. Peer set: DMart, Aditya Birla Fashion, Shoppers Stop,
V-Mart, Vedant Fashions, Page Industries, Bata India.

**Blend:** 60% DCF + 40% comps → headline fair value → rating
(Buy > +15%, Sell < −10%, else Hold).

---

## Project structure

```
trent-equity-valuation/
├── valuation/
│   ├── assumptions.py   # every input + justification (edit here)
│   ├── data.py          # Yahoo Finance pull, INR-crore snapshot, fallbacks
│   ├── dcf.py           # FCFF projection, WACC, terminal value, sensitivity
│   ├── comps.py         # peer multiples -> implied value
│   └── report.py        # blend, recommendation, charts, Excel export
├── examples/
│   └── run_valuation.py # end-to-end run (live, with offline fallback)
├── tests/
│   └── test_valuation.py
├── outputs/             # football field, sensitivity heatmap, Excel model
└── requirements.txt
```

---

## Quickstart

```bash
git clone <this-repo-url>
cd trent-equity-valuation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m pytest -q              # 10 tests, no network needed
python -m examples.run_valuation # full valuation + charts + Excel
```

### Outputs
- `outputs/football_field.png` — valuation ranges (DCF, comps) vs market price
- `outputs/dcf_sensitivity.png` — fair value across WACC × terminal growth
- `outputs/Trent_valuation_model.xlsx` — Summary, DCF, Comps, Sensitivity sheets

---

## Key assumptions (defaults)

| Input | Value | Rationale |
|---|---|---|
| Revenue growth (yrs 1-5) | 30% → 12% | Fast but fading from recent hyper-growth |
| EBIT margin | 11.5% → 12.4% | Modest operating leverage on a maturing base |
| WACC | ~12% | CAPM, beta 0.95, ERP 6%, Rf 7% |
| Terminal growth | 6% | ~ long-run nominal GDP |
| Exit EV/EBITDA | 22x | Premium retailer cross-check |
| Tax | 25% | Indian new-regime corporate rate |

> **Note on beta:** Yahoo reports a beta of ~0.35 for Trent, which is implausibly
> low for a high-growth discretionary retailer and would understate the cost of
> equity. The model uses 0.95 by default; adjust in `assumptions.py` to test it.

---

## Testing

```bash
python -m pytest -q
```
Covers DCF mechanics (higher WACC lowers value, terminal-growth monotonicity,
WACC > g guard), scenario ordering (bear < base < bull), recommendation bands,
and balance-sheet maths — all offline.

## License
MIT — see `LICENSE`.
