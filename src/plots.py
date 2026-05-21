from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from .backtest import SINGLE_SIGNAL_ORDER
from .config import BACKTEST_DIR, PLOT_DIR, SIGNAL_DIR


def _signal_plot(signal_name: str) -> None:
    df = pd.read_csv(SIGNAL_DIR / f"{signal_name}.csv", parse_dates=["date"])
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(df["date"], df["raw_value"], color="tab:blue", label="raw_value")
    ax1.set_title(signal_name)
    ax1.set_ylabel("raw_value", color="tab:blue")
    ax2 = ax1.twinx()
    ax2.step(df["date"], df["signal"], where="mid", color="tab:red", label="signal")
    ax2.set_ylabel("signal", color="tab:red")
    ax2.set_ylim(-1.2, 1.2)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / f"signals_{signal_name}.png", dpi=150)
    plt.close(fig)


def plot_all_signals() -> None:
    for name in ["erp", "margin_buy", "bollinger", "advance_decline", "option_pcr", "option_iv", "futures_member"]:
        _signal_plot(name)


def plot_factors() -> None:
    df = pd.read_csv("data/processed/factors/factors.csv", parse_dates=["date"])
    fig, ax = plt.subplots(figsize=(12, 6))
    for col in ["valuation_factor", "funding_factor", "technical_factor", "sentiment_factor", "left_factor", "right_factor", "final_score"]:
        ax.plot(df["date"], df[col], label=col, linewidth=1)
    ax.legend(loc="upper left", ncol=2, fontsize=8)
    ax.set_title("Factor Series")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "factors.png", dpi=150)
    plt.close(fig)


def plot_nav() -> None:
    df = pd.read_csv("data/processed/backtest/backtest.csv", parse_dates=["date"])
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["date"], df["nav"], label="strategy_nav")
    ax.plot(df["date"], df["asset_nav"], label="asset_nav")
    ax.legend()
    ax.set_title("Final Strategy NAV")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "final_strategy_nav.png", dpi=150)
    plt.close(fig)


def plot_single_signal_nav() -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    for name in SINGLE_SIGNAL_ORDER:
        df = pd.read_csv(BACKTEST_DIR / "single_signals" / f"{name}.csv", parse_dates=["date"])
        ax.plot(df["date"], df["nav"], label=name, linewidth=1)
    ax.legend(loc="upper left", ncol=2, fontsize=8)
    ax.set_title("Single Signal Strategy NAV")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "single_signal_nav.png", dpi=150)
    plt.close(fig)
