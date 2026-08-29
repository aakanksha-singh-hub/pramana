"""B2 - payer session features.

The raw telemetry is emitted by ledger.attach_sessions from a duress latent.
This module is the projection onto the pre-registered column list; keeping it
explicit means the arm definition cannot drift from PREREGISTRATION.md.
"""

from __future__ import annotations

import pandas as pd

from . import B2_COLS


def build(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in B2_COLS if c not in df.columns]
    if missing:
        raise KeyError(f"session telemetry missing columns: {missing}")
    return df[B2_COLS].copy()
