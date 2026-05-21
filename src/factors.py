from __future__ import annotations

import numpy as np
import pandas as pd

from .config import FACTOR_DIR
from .data_io import processed_signal_path, read_csv_file, save_csv_file


def _load_signal(name: str) -> pd.DataFrame:
    df = read_csv_file(processed_signal_path(name))
    return df.rename(columns={"raw_value": f"{name}_raw_value", "signal": f"{name}_signal"})


def compute_factors() -> pd.DataFrame:
    names = ["erp", "margin_buy", "bollinger", "advance_decline", "option_pcr", "option_iv", "futures_member"]
    frames = [_load_signal(name) for name in names]
    base = frames[0]
    for frame in frames[1:]:
        base = base.merge(frame, on="date", how="outer")
    base = base.sort_values("date")

    base["valuation_factor"] = base["erp_signal"]
    base["funding_factor"] = base["margin_buy_signal"]
    base["technical_factor"] = base[["bollinger_signal", "advance_decline_signal"]].mean(axis=1)
    base["sentiment_factor"] = base[["option_pcr_signal", "option_iv_signal", "futures_member_signal"]].mean(axis=1)
    base["left_factor"] = base[["valuation_factor", "sentiment_factor"]].mean(axis=1)
    base["right_factor"] = base[["funding_factor", "technical_factor"]].mean(axis=1)
    base["final_score"] = base[["left_factor", "right_factor"]].mean(axis=1)
    base["final_signal"] = np.sign(base["final_score"]).fillna(0).astype(int)

    out = base[
        [
            "date",
            "valuation_factor",
            "funding_factor",
            "technical_factor",
            "sentiment_factor",
            "left_factor",
            "right_factor",
            "final_score",
            "final_signal",
        ]
    ].copy()
    save_csv_file(out, FACTOR_DIR / "factors.csv")
    return out
