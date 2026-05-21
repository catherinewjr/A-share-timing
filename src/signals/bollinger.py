from __future__ import annotations

import pandas as pd

from ..config import BOLL_STD, BOLL_WINDOW
from ..data_io import raw_path, processed_signal_path, read_csv_file, save_csv_file
from .base import bollinger_signal, validate_signal_frame


def compute() -> pd.DataFrame:
    df = read_csv_file(raw_path("bollinger_price_raw.csv"))
    df = df[df["date"] <= pd.Timestamp("2025-04-30")].copy()
    df["raw_value"] = df["close"]
    df["signal"] = bollinger_signal(df["raw_value"], window=BOLL_WINDOW, std=BOLL_STD, mode="trend")
    out = validate_signal_frame(df[["date", "raw_value", "signal"]])
    save_csv_file(out, processed_signal_path("bollinger"))
    return out
