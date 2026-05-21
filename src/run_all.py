from __future__ import annotations

from datetime import datetime

import pandas as pd

from . import backtest, factors, plots
from .config import DOCS_DIR, END_DATE, LOG_DIR, PROJECT_ROOT, RAW_DIR
from .data_io import ensure_dirs, processed_signal_path, read_csv_file, write_log
from .signals import advance_decline, bollinger, erp, futures_member, margin_buy, option_iv, option_pcr


SIGNAL_ORDER = ["erp", "margin_buy", "bollinger", "advance_decline", "option_pcr", "option_iv", "futures_member"]


def _signal_docs_table() -> list[dict[str, object]]:
    assumptions = {
        "erp": "ERP = 1 / pe_ttm - treasury_10y_yield, mapped by a 1250-day rolling percentile in persistent trend mode.",
        "margin_buy": "Use market-level margin_buy_total and map it with trend Bollinger. The state is held until the opposite breakout appears.",
        "bollinger": "Use 000985.XSHG close and map it with trend Bollinger using window=20 and std=2.",
        "advance_decline": "Use MA60-smoothed (up_amount - down_amount) / total_amount, convert to month-end values, compute monthly YoY direction, then forward-fill back to trading days.",
        "option_pcr": "Use pcr_inverse = 1 / amount_pcr = call_amount / put_amount, then apply reverse Bollinger with persistent state carry-forward.",
        "option_iv": "Use the mean of iv_105_95, iv_110_90, and iv_120_80, average across ETF underlyings by date, smooth with MA20, then apply reverse Bollinger with persistent state carry-forward.",
        "futures_member": "Use IF only and apply trend Bollinger to long_short_ratio with persistent state carry-forward.",
    }

    rows: list[dict[str, object]] = []
    for name in SIGNAL_ORDER:
        df = read_csv_file(processed_signal_path(name))
        rows.append(
            {
                "signal_name": name,
                "start_date": str(df["date"].min().date()),
                "end_date": str(df["date"].max().date()),
                "missing_ratio_raw_value": float(df["raw_value"].isna().mean()),
                "assumption": assumptions[name],
            }
        )
    return rows


def _known_deviations() -> list[str]:
    return [
        "advance_decline now follows the mentor direction more closely, but the published report still does not expose a line-by-line official daily implementation; the current month-end YoY mapping is an approximation.",
        "option_iv uses daily equal-weight averaging across 50ETF / 300ETF / 500ETF before MA20 smoothing. This remains a practical reconstruction rather than a guaranteed report-identical weighting rule.",
        "ERP raw pe_ttm contains missing values; no aggressive filling or parameter tuning is applied.",
    ]


def _readme_lines_en(signal_rows: list[dict[str, object]]) -> list[str]:
    lines = [
        "# Huatai Timing Reproduction",
        "",
        "## Status",
        "",
        "This folder contains the current strategy-reproduction pipeline. The raw CSV files in `data/raw/` are treated as fixed inputs and are not modified by the pipeline.",
        "",
        "## Project Structure",
        "",
        "```text",
        "data/raw -> fixed raw CSV inputs",
        "data/processed/signals -> 7 single-signal CSV files",
        "data/processed/factors -> factor-combination CSV",
        "data/processed/backtest -> backtest daily CSV",
        "outputs/plots -> PNG charts",
        "outputs/tables -> performance and summary tables",
        "outputs/logs -> pipeline_log.md",
        "src/ -> reproducible source code",
        "```",
        "",
        "## Reproduction Flow",
        "",
        "1. Read raw CSV files from `data/raw/`.",
        "2. Compute 7 single signals.",
        "3. Combine them into valuation / funding / technical / sentiment / left / right / final factors.",
        "4. Backtest with `final_signal.shift(1)` on 000985.XSHG close returns.",
        "5. Generate plots, tables, and logs.",
        "",
        "## Run Command",
        "",
        "```bash",
        "python main.py",
        "```",
        "",
        "## Mentor-Document Signal Update",
        "",
        "- This round rewrites the seven signals as persistent-state signals.",
        "- Bollinger and rolling-percentile mappings now switch state only on threshold breakouts and keep that state until the opposite breakout occurs.",
        "- PCR now uses reciprocal + reverse Bollinger.",
        "- IV now uses MA20 smoothing + reverse Bollinger.",
        "- Futures member positioning now uses trend Bollinger.",
        "- Advance/decline now uses MA60 smoothing + month-end YoY direction + forward-fill back to trading days.",
        "",
        "## Auxiliary Reports Used To Confirm Direction",
        "",
        "- `A股择时之期权期货市场指标` (2024-07-14)",
        "- `A股择时之情绪面指标测试` (2021-02-04)",
        "- `A股择时之技术面指标测试` (2021-08-17)",
        "",
        "## Core Outputs",
        "",
        "- `data/processed/signals/*.csv`",
        "- `data/processed/factors/factors.csv`",
        "- `data/processed/backtest/backtest.csv`",
        "- `outputs/tables/performance.csv`",
        "- `outputs/plots/*.png`",
        "",
        "## Signal Missing Ratios",
        "",
    ]
    for row in signal_rows:
        lines.append(f"- `{row['signal_name']}`: raw_value missing ratio = {row['missing_ratio_raw_value']:.6f}")
    lines.extend(["", "## Signal Logic Notes", ""])
    for row in signal_rows:
        lines.append(f"- `{row['signal_name']}`: {row['assumption']}")
    lines.extend(["", "## Known Deviations vs. Report Logic", ""])
    for item in _known_deviations():
        lines.append(f"- {item}")
    return lines


def _readme_lines_zh(signal_rows: list[dict[str, object]]) -> list[str]:
    lines = [
        "# 华泰择时复现说明",
        "",
        "## 当前状态",
        "",
        "当前目录包含完整的策略复现流水线。`data/raw/` 下的原始 CSV 被视为固定输入，主流程不会修改这些文件。",
        "",
        "## 项目结构",
        "",
        "```text",
        "data/raw -> 固定原始 CSV 输入",
        "data/processed/signals -> 7 个单信号 CSV",
        "data/processed/factors -> 因子合成 CSV",
        "data/processed/backtest -> 回测日度结果 CSV",
        "outputs/plots -> PNG 图表",
        "outputs/tables -> performance 和 summary 表",
        "outputs/logs -> pipeline_log.md",
        "src/ -> 可复现源码",
        "```",
        "",
        "## 复现流程",
        "",
        "1. 从 `data/raw/` 读取原始 CSV。",
        "2. 计算 7 个单信号。",
        "3. 合成为估值 / 资金 / 技术 / 情绪 / 左侧 / 右侧 / 最终信号。",
        "4. 对 `000985.XSHG` 收盘价收益使用 `final_signal.shift(1)` 做回测。",
        "5. 生成图表、结果表和日志。",
        "",
        "## 运行命令",
        "",
        "```bash",
        "python main.py",
        "```",
        "",
        "## 本轮信号层修正",
        "",
        "- 本轮按 mentor 文档把 7 个信号统一改成持续型信号。",
        "- BOLL / 分位数信号现在只有在突破阈值时才切换状态，中间区域保持上一状态。",
        "- PCR 改为倒数口径 + 反向布林带。",
        "- IV 改为 MA20 平滑 + 反向布林带。",
        "- 期货会员持仓改为正向布林带。",
        "- 个股涨跌成交额占比差改为 MA60 平滑 + 月末同比方向 + 日频前向填充。",
        "",
        "## 辅助研报",
        "",
        "- 《A股择时之期权期货市场指标》（2024-07-14）",
        "- 《A股择时之情绪面指标测试》（2021-02-04）",
        "- 《A股择时之技术面指标测试》（2021-08-17）",
        "",
        "## 核心输出",
        "",
        "- `data/processed/signals/*.csv`",
        "- `data/processed/factors/factors.csv`",
        "- `data/processed/backtest/backtest.csv`",
        "- `outputs/tables/performance.csv`",
        "- `outputs/plots/*.png`",
        "",
        "## 各信号缺失率",
        "",
    ]
    for row in signal_rows:
        lines.append(f"- `{row['signal_name']}`：`raw_value` 缺失率 = {row['missing_ratio_raw_value']:.6f}")
    lines.extend(["", "## 各信号实现说明", ""])
    for row in signal_rows:
        lines.append(f"- `{row['signal_name']}`：{row['assumption']}")
    lines.extend(["", "## 与研报口径可能存在的偏差", ""])
    for item in _known_deviations():
        lines.append(f"- {item}")
    return lines


def _write_text_docs(signal_rows: list[dict[str, object]]) -> None:
    (DOCS_DIR / "README.md").write_text("\n".join(_readme_lines_en(signal_rows)) + "\n", encoding="utf-8")
    (DOCS_DIR / "README_zh.md").write_text("\n".join(_readme_lines_zh(signal_rows)) + "\n", encoding="utf-8")


def _write_pipeline_log(backtest_df: pd.DataFrame, signal_rows: list[dict[str, object]]) -> None:
    lines = [
        "# Pipeline Log",
        "",
        f"- run_time: {datetime.now().isoformat(timespec='seconds')}",
        f"- project_root: {PROJECT_ROOT}",
        f"- end_date: {END_DATE}",
        "- input_files:",
        "  - data/raw/erp_raw.csv",
        "  - data/raw/margin_buy_total.csv",
        "  - data/raw/bollinger_price_raw.csv",
        "  - data/raw/advance_decline_amount_daily.csv",
        "  - data/raw/option_50etf_pcr_daily.csv",
        "  - data/raw/option_iv_ratio_daily.csv",
        "  - data/raw/futures_member_long_short_daily.csv",
        "- output_files:",
        "  - data/processed/signals/*.csv",
        "  - data/processed/factors/factors.csv",
        "  - data/processed/backtest/backtest.csv",
        "  - outputs/tables/performance.csv",
        "  - outputs/plots/*.png",
        f"- backtest_start_date: {backtest_df['date'].min().date()}",
        f"- backtest_end_date: {backtest_df['date'].max().date()}",
        "- used_shift_1: True",
        "",
        "## Mentor-Document Signal Update",
        "",
        "- Persistent-state signal logic is now used throughout the signal layer.",
        "- PCR uses reciprocal + reverse Bollinger.",
        "- IV uses MA20 + reverse Bollinger.",
        "- Futures member positioning uses trend Bollinger.",
        "- Advance/decline uses MA60 + month-end YoY direction + forward-fill back to daily dates.",
        "",
        "## Signal Date Ranges / Missing Ratios",
        "",
    ]
    for row in signal_rows:
        lines.append(
            f"- {row['signal_name']}: {row['start_date']} -> {row['end_date']}, raw_value_missing={row['missing_ratio_raw_value']:.6f}"
        )
    lines.extend(
        [
            "",
            "## Still Requires Manual Confirmation",
            "",
            "- advance_decline monthly YoY transformation is still an approximation because the target report does not publish a fully explicit daily formula.",
            "- option_iv daily aggregation across 50ETF / 300ETF / 500ETF remains a practical reconstruction, not a guaranteed report-identical weighting rule.",
            "- ERP raw pe_ttm contains missing values and is not aggressively filled.",
        ]
    )
    write_log("\n".join(lines) + "\n", LOG_DIR / "pipeline_log.md", mode="w")


def _write_reference_docs() -> None:
    raw_file_map = {
        "erp_raw.csv": "ERP input: date, pe_ttm, treasury_10y_yield",
        "margin_buy_total.csv": "Margin-buy input: date, margin_buy_total",
        "bollinger_price_raw.csv": "Price input for Bollinger and backtest asset returns",
        "advance_decline_amount_daily.csv": "Advance/decline input: up_amount, down_amount, total_amount",
        "option_50etf_pcr_daily.csv": "PCR input: put/call volume, amount, open interest and PCR ratios",
        "option_iv_ratio_daily.csv": "IV ratio input: daily 105/95, 110/90, 120/80 ratios",
        "futures_member_long_short_daily.csv": "Futures member input: IF/IH/IC daily long/short top20 summaries",
    }

    lines_en = [
        "# Data Dictionary",
        "",
        "Archive/reference only. This file documents the raw CSV files used by the reproduction pipeline.",
        "",
    ]
    lines_zh = [
        "# 数据字典",
        "",
        "归档 / 参考用途。本文档记录当前复现流水线使用的 raw CSV 文件。",
        "",
    ]

    for filename, desc in raw_file_map.items():
        df = pd.read_csv(RAW_DIR / filename)
        columns = ", ".join(df.columns)
        start_date = df["date"].min() if "date" in df.columns else "n/a"
        end_date = df["date"].max() if "date" in df.columns else "n/a"
        missing_ratio = {col: float(df[col].isna().mean()) for col in df.columns}
        lines_en.extend(
            [
                f"## {filename}",
                "",
                f"- description: {desc}",
                f"- columns: {columns}",
                f"- rows: {len(df)}",
                f"- start_date: {start_date}",
                f"- end_date: {end_date}",
                f"- missing_ratio: {missing_ratio}",
                "",
            ]
        )
        lines_zh.extend(
            [
                f"## {filename}",
                "",
                f"- 说明：{desc}",
                f"- 字段：{columns}",
                f"- 行数：{len(df)}",
                f"- 起始日期：{start_date}",
                f"- 结束日期：{end_date}",
                f"- 缺失率：{missing_ratio}",
                "",
            ]
        )

    (DOCS_DIR / "data_dictionary.md").write_text("\n".join(lines_en) + "\n", encoding="utf-8")
    (DOCS_DIR / "data_dictionary_zh.md").write_text("\n".join(lines_zh) + "\n", encoding="utf-8")


def _update_docs(backtest_df: pd.DataFrame) -> None:
    signal_rows = _signal_docs_table()
    _write_text_docs(signal_rows)
    _write_reference_docs()
    _write_pipeline_log(backtest_df, signal_rows)


def main() -> None:
    ensure_dirs()
    erp.compute()
    margin_buy.compute()
    bollinger.compute()
    advance_decline.compute()
    option_pcr.compute()
    option_iv.compute()
    futures_member.compute()
    factors.compute_factors()
    backtest_df, _perf_df = backtest.run_backtest()
    backtest.run_single_signal_backtests()
    plots.plot_all_signals()
    plots.plot_factors()
    plots.plot_nav()
    plots.plot_single_signal_nav()
    _update_docs(backtest_df)
