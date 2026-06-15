"""Trent Ltd equity valuation: DCF + trading comparables."""
from .assumptions import Assumptions, TRENT_DEFAULTS
from .data import CompanySnapshot, fetch_snapshot
from .dcf import run_dcf, DCFResult
from .comps import run_comps, CompsResult

__all__ = [
    "Assumptions",
    "TRENT_DEFAULTS",
    "CompanySnapshot",
    "fetch_snapshot",
    "run_dcf",
    "DCFResult",
    "run_comps",
    "CompsResult",
]
__version__ = "1.0.0"
