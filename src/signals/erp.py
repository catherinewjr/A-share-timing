from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import ERP_PERCENTILE_WINDOW, HIGH_Q, LOW_Q
from ..data_io import raw_path, processed_signal_path, read_csv_file, save_csv_file
from .base import rolling_percentile_signal, validate_signal_frame


def compute() -> pd.DataFrame:
    df = read_csv_file(raw_path("erp_raw.csv"))
    df = df[df["date"] <= pd.Timestamp("2025-04-30")].copy()
    df["raw_value"] = 1.0 / df["pe_ttm"] - df["treasury_10y_yield"]
    df["signal"] = rolling_percentile_signal(
        df["raw_value"],
        window=ERP_PERCENTILE_WINDOW,
        high_q=HIGH_Q,
        low_q=LOW_Q,
        mode="trend",
    )
    out = validate_signal_frame(df[["date", "raw_value", "signal"]])
    save_csv_file(out, processed_signal_path("erp"))
    return out
