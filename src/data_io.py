from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import BACKTEST_DIR, DOCS_DIR, FACTOR_DIR, LOG_DIR, OUTPUT_DIR, PLOT_DIR, PROCESSED_DIR, PROJECT_ROOT, RAW_DIR, SIGNAL_DIR, TABLE_DIR


def ensure_dirs() -> None:
    for path in [
        PROCESSED_DIR,
        SIGNAL_DIR,
        FACTOR_DIR,
        BACKTEST_DIR,
        OUTPUT_DIR,
        PLOT_DIR,
        TABLE_DIR,
        LOG_DIR,
        DOCS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_csv_file(path: Path | str, parse_dates: Iterable[str] | None = ("date",)) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    df = pd.read_csv(path)
    if parse_dates:
        for col in parse_dates:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
    return df


def save_csv_file(df: pd.DataFrame, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False, encoding="utf-8-sig")


def check_missing_ratio(df: pd.DataFrame) -> dict[str, float]:
    return {str(col): float(df[col].isna().mean()) for col in df.columns}


def write_log(text: str, path: Path | str, mode: str = "a") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode, encoding="utf-8") as f:
        f.write(text)


def raw_path(name: str) -> Path:
    return RAW_DIR / name


def processed_signal_path(name: str) -> Path:
    return SIGNAL_DIR / f"{name}.csv"
