from __future__ import annotations

import pandas as pd

from ..config import BOLL_STD, BOLL_WINDOW
from ..data_io import raw_path, processed_signal_path, read_csv_file, save_csv_file
from .base import bollinger_signal, moving_average, validate_signal_frame


def compute() -> pd.DataFrame:
    df = read_csv_file(raw_path("option_iv_ratio_daily.csv"))
    df = df[df["date"] <= pd.Timestamp("2025-04-30")].copy()
    iv_cols = ["iv_105_95", "iv_110_90", "iv_120_80"]
    df["row_mean"] = df[iv_cols].mean(axis=1)
    daily = df.groupby("date", as_index=False)["row_mean"].mean().rename(columns={"row_mean": "composite_iv"})
    daily["raw_value"] = moving_average(daily["composite_iv"], BOLL_WINDOW)
    daily["signal"] = bollinger_signal(
        daily["raw_value"],
        window=BOLL_WINDOW,
        std=BOLL_STD,
        mode="reverse",
    )
    out = validate_signal_frame(daily[["date", "raw_value", "signal"]])
    save_csv_file(out, processed_signal_path("option_iv"))
    return out
