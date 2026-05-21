from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import ADVANCE_DECLINE_MA
from ..data_io import raw_path, processed_signal_path, read_csv_file, save_csv_file
from .base import moving_average, validate_signal_frame


def compute() -> pd.DataFrame:
    df = read_csv_file(raw_path("advance_decline_amount_daily.csv"))
    df = df[df["date"] <= pd.Timestamp("2025-04-30")].copy()
    ad_ratio = (df["up_amount"] - df["down_amount"]) / df["total_amount"].replace(0, pd.NA)
    df["raw_value"] = moving_average(ad_ratio.astype("float64"), ADVANCE_DECLINE_MA)

    monthly = (
        df.set_index("date")[["raw_value"]]
        .resample("M")
        .last()
        .rename_axis("date")
        .reset_index()
    )
    monthly["yoy_change"] = monthly["raw_value"] - monthly["raw_value"].shift(12)
    monthly["monthly_signal"] = 0
    monthly.loc[monthly["yoy_change"] > 0, "monthly_signal"] = 1
    monthly.loc[monthly["yoy_change"] < 0, "monthly_signal"] = -1
    monthly["monthly_signal"] = monthly["monthly_signal"].mask(monthly["monthly_signal"].eq(0), np.nan).ffill().fillna(0).astype(int)

    merged = df[["date", "raw_value"]].merge(monthly[["date", "monthly_signal"]], on="date", how="left")
    merged["signal"] = merged["monthly_signal"].ffill().fillna(0).astype(int)
    df["signal"] = merged["signal"]
    out = validate_signal_frame(df[["date", "raw_value", "signal"]])
    save_csv_file(out, processed_signal_path("advance_decline"))
    return out
