from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import BACKTEST_DIR, FEE_RATE, FACTOR_DIR, RAW_DIR, SIGNAL_DIR, TABLE_DIR, TRADING_DAYS
from .data_io import save_csv_file


SINGLE_SIGNAL_ORDER = ["erp", "margin_buy", "bollinger", "advance_decline", "option_pcr", "option_iv", "futures_member"]


def _max_drawdown(nav: pd.Series) -> float:
    running_max = nav.cummax()
    dd = nav / running_max - 1.0
    return float(dd.min())


def _performance(backtest: pd.DataFrame) -> pd.DataFrame:
    returns = backtest["strategy_return"].dropna()
    nav = backtest["nav"].dropna()
    n = len(returns)
    ann_return = float((1 + returns).prod() ** (TRADING_DAYS / n) - 1) if n else 0.0
    ann_vol = float(returns.std(ddof=0) * math.sqrt(TRADING_DAYS)) if n else 0.0
    sharpe = ann_return / ann_vol if ann_vol else 0.0
    mdd = _max_drawdown(nav) if len(nav) else 0.0
    calmar = ann_return / abs(mdd) if mdd else 0.0
    active = backtest.loc[backtest["position"].ne(0), "strategy_return"]
    win_rate = float((active > 0).mean()) if len(active) else 0.0
    return pd.DataFrame(
        [
            {
                "annual_return": ann_return,
                "annual_volatility": ann_vol,
                "sharpe": sharpe,
                "max_drawdown": mdd,
                "calmar": calmar,
                "win_rate": win_rate,
            }
        ]
    )


def _benchmark_performance(backtest: pd.DataFrame) -> dict[str, float]:
    benchmark = backtest[["date", "asset_return", "asset_nav"]].copy()
    benchmark = benchmark.rename(columns={"asset_return": "strategy_return", "asset_nav": "nav"})
    benchmark["position"] = 1
    perf = _performance(benchmark).iloc[0].to_dict()
    return {f"benchmark_{key}": value for key, value in perf.items()}


def _run_signal_backtest(
    signal_df: pd.DataFrame,
    signal_col: str,
    output_signal_col: str,
    align_to_signal_dates: bool = False,
) -> pd.DataFrame:
    price = pd.read_csv(RAW_DIR / "bollinger_price_raw.csv", parse_dates=["date"])
    if align_to_signal_dates:
        df = signal_df[["date", signal_col]].merge(price[["date", "close"]], on="date", how="left")
    else:
        df = price[["date", "close"]].merge(signal_df[["date", signal_col]], on="date", how="left")
    df = df.rename(columns={signal_col: output_signal_col}).sort_values("date")
    df["asset_return"] = df["close"].pct_change()
    df["position"] = df[output_signal_col].fillna(0).shift(1).fillna(0)
    df["turnover"] = df["position"].diff().abs().fillna(df["position"].abs())
    df["strategy_return_gross"] = df["position"] * df["asset_return"]
    df["strategy_return"] = df["strategy_return_gross"] - df["turnover"] * FEE_RATE
    df["nav"] = (1 + df["strategy_return"].fillna(0)).cumprod()
    df["asset_nav"] = (1 + df["asset_return"].fillna(0)).cumprod()
    return df


def run_backtest() -> tuple[pd.DataFrame, pd.DataFrame]:
    factors = pd.read_csv(FACTOR_DIR / "factors.csv", parse_dates=["date"])
    df = _run_signal_backtest(factors, "final_signal", "final_signal")

    out = df[["date", "close", "asset_return", "final_signal", "position", "turnover", "strategy_return", "nav", "asset_nav"]].copy()
    save_csv_file(out, BACKTEST_DIR / "backtest.csv")

    perf = _performance(out)
    save_csv_file(perf, TABLE_DIR / "performance.csv")
    summary = pd.DataFrame(
        [
            {
                "start_date": str(out["date"].min().date()),
                "end_date": str(out["date"].max().date()),
                "num_rows": len(out),
                "num_active_days": int((out["position"] != 0).sum()),
                "used_shift_1": True,
                "fee_rate": FEE_RATE,
            }
        ]
    )
    save_csv_file(summary, TABLE_DIR / "summary.csv")
    return out, perf


def run_single_signal_backtests() -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}
    performance_rows = []
    out_dir = BACKTEST_DIR / "single_signals"
    for name in SINGLE_SIGNAL_ORDER:
        signal = pd.read_csv(SIGNAL_DIR / f"{name}.csv", parse_dates=["date"])
        df = _run_signal_backtest(signal, "signal", "signal", align_to_signal_dates=True)
        out = df[["date", "close", "asset_return", "signal", "position", "turnover", "strategy_return", "nav", "asset_nav"]].copy()
        save_csv_file(out, out_dir / f"{name}.csv")
        results[name] = out

        perf = _performance(out).iloc[0].to_dict()
        benchmark_perf = _benchmark_performance(out)
        perf.update(
            {
                "signal_name": name,
                "start_date": str(out["date"].min().date()),
                "end_date": str(out["date"].max().date()),
                "num_rows": len(out),
                "num_active_days": int((out["position"] != 0).sum()),
                "used_shift_1": True,
                "fee_rate": FEE_RATE,
            }
        )
        perf.update(benchmark_perf)
        performance_rows.append(perf)

    perf_df = pd.DataFrame(performance_rows)
    ordered_cols = [
        "signal_name",
        "start_date",
        "end_date",
        "num_rows",
        "num_active_days",
        "used_shift_1",
        "fee_rate",
        "annual_return",
        "annual_volatility",
        "sharpe",
        "max_drawdown",
        "calmar",
        "win_rate",
        "benchmark_annual_return",
        "benchmark_annual_volatility",
        "benchmark_sharpe",
        "benchmark_max_drawdown",
        "benchmark_calmar",
        "benchmark_win_rate",
    ]
    perf_df = perf_df[ordered_cols]
    save_csv_file(perf_df, TABLE_DIR / "single_signal_performance.csv")
    return results, perf_df
