from __future__ import annotations

import numpy as np
import pandas as pd


def moving_average(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def continuous_signal(event_signal: pd.Series) -> pd.Series:
    out = event_signal.copy().astype("float64")
    out = out.replace(0, np.nan).ffill().fillna(0)
    return out.astype(int)


def bollinger_signal(series: pd.Series, window: int, std: float, mode: str = "trend") -> pd.Series:
    ma = series.rolling(window=window, min_periods=window).mean()
    sigma = series.rolling(window=window, min_periods=window).std(ddof=0)
    upper = ma + std * sigma
    lower = ma - std * sigma

    event = pd.Series(0, index=series.index, dtype="int64")
    if mode == "trend":
        event = event.mask(series > upper, 1)
        event = event.mask(series < lower, -1)
    elif mode == "reverse":
        event = event.mask(series > upper, -1)
        event = event.mask(series < lower, 1)
    else:
        raise ValueError(f"Unsupported bollinger mode: {mode}")
    signal = continuous_signal(event)
    signal = signal.where(series.notna(), 0).astype(int)
    return signal


def rolling_percentile_signal(
    series: pd.Series,
    window: int,
    high_q: float,
    low_q: float,
    mode: str = "trend",
) -> pd.Series:
    high = series.rolling(window=window, min_periods=window).quantile(high_q)
    low = series.rolling(window=window, min_periods=window).quantile(low_q)
    event = pd.Series(0, index=series.index, dtype="int64")
    if mode == "trend":
        event = event.mask(series >= high, 1)
        event = event.mask(series <= low, -1)
    elif mode == "reverse":
        event = event.mask(series >= high, -1)
        event = event.mask(series <= low, 1)
    else:
        raise ValueError(f"Unsupported percentile mode: {mode}")
    signal = continuous_signal(event)
    signal = signal.where(series.notna(), 0).astype(int)
    return signal


def validate_signal_frame(df: pd.DataFrame) -> pd.DataFrame:
    required = ["date", "raw_value", "signal"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Signal frame missing columns: {missing}")
    out = df[required].copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.sort_values("date").drop_duplicates(subset=["date"])
    out["signal"] = out["signal"].fillna(0).astype(int)
    invalid = set(out["signal"].dropna().unique()) - {-1, 0, 1}
    if invalid:
        raise ValueError(f"Invalid signal values: {invalid}")
    return out
