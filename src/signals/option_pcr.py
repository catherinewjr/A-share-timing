from __future__ import annotations

import pandas as pd

from ..config import BOLL_STD, BOLL_WINDOW
from ..data_io import raw_path, processed_signal_path, read_csv_file, save_csv_file
from .base import bollinger_signal, validate_signal_frame


def compute() -> pd.DataFrame:
    df = read_csv_file(raw_path("option_50etf_pcr_daily.csv"))
    df = df[df["date"] <= pd.Timestamp("2025-04-30")].copy()
    # Auxiliary report confirmation: use the reciprocal form for trading PCR metrics.
    # The raw file stores amount_pcr = put_amount / call_amount, so pcr_inverse = call_amount / put_amount.
    df["raw_value"] = 1.0 / df["amount_pcr"]
    df["signal"] = bollinger_signal(df["raw_value"], window=BOLL_WINDOW, std=BOLL_STD, mode="reverse")
    out = validate_signal_frame(df[["date", "raw_value", "signal"]])
    save_csv_file(out, processed_signal_path("option_pcr"))
    return out
