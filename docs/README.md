# Huatai Timing Reproduction

## Status

This folder contains the current strategy-reproduction pipeline. The raw CSV files in `data/raw/` are treated as fixed inputs and are not modified by the pipeline.

## Project Structure

```text
data/raw -> fixed raw CSV inputs
data/processed/signals -> 7 single-signal CSV files
data/processed/factors -> factor-combination CSV
data/processed/backtest -> backtest daily CSV
outputs/plots -> PNG charts
outputs/tables -> performance and summary tables
outputs/logs -> pipeline_log.md
src/ -> reproducible source code
```

## Reproduction Flow

1. Read raw CSV files from `data/raw/`.
2. Compute 7 single signals.
3. Combine them into valuation / funding / technical / sentiment / left / right / final factors.
4. Backtest with `final_signal.shift(1)` on 000985.XSHG close returns.
5. Generate plots, tables, and logs.

## Run Command

```bash
python main.py
```

## Mentor-Document Signal Update

- This round rewrites the seven signals as persistent-state signals.
- Bollinger and rolling-percentile mappings now switch state only on threshold breakouts and keep that state until the opposite breakout occurs.
- PCR now uses reciprocal + reverse Bollinger.
- IV now uses MA20 smoothing + reverse Bollinger.
- Futures member positioning now uses trend Bollinger.
- Advance/decline now uses MA60 smoothing + month-end YoY direction + forward-fill back to trading days.

## Auxiliary Reports Used To Confirm Direction

- `A股择时之期权期货市场指标` (2024-07-14)
- `A股择时之情绪面指标测试` (2021-02-04)
- `A股择时之技术面指标测试` (2021-08-17)

## Core Outputs

- `data/processed/signals/*.csv`
- `data/processed/factors/factors.csv`
- `data/processed/backtest/backtest.csv`
- `outputs/tables/performance.csv`
- `outputs/plots/*.png`

## Signal Missing Ratios

- `erp`: raw_value missing ratio = 0.102929
- `margin_buy`: raw_value missing ratio = 0.000000
- `bollinger`: raw_value missing ratio = 0.000000
- `advance_decline`: raw_value missing ratio = 0.015856
- `option_pcr`: raw_value missing ratio = 0.000000
- `option_iv`: raw_value missing ratio = 0.009586
- `futures_member`: raw_value missing ratio = 0.000000

## Signal Logic Notes

- `erp`: ERP = 1 / pe_ttm - treasury_10y_yield, mapped by a 1250-day rolling percentile in persistent trend mode.
- `margin_buy`: Use market-level margin_buy_total and map it with trend Bollinger. The state is held until the opposite breakout appears.
- `bollinger`: Use 000985.XSHG close and map it with trend Bollinger using window=20 and std=2.
- `advance_decline`: Use MA60-smoothed (up_amount - down_amount) / total_amount, convert to month-end values, compute monthly YoY direction, then forward-fill back to trading days.
- `option_pcr`: Use pcr_inverse = 1 / amount_pcr = call_amount / put_amount, then apply reverse Bollinger with persistent state carry-forward.
- `option_iv`: Use the mean of iv_105_95, iv_110_90, and iv_120_80, average across ETF underlyings by date, smooth with MA20, then apply reverse Bollinger with persistent state carry-forward.
- `futures_member`: Use IF only and apply trend Bollinger to long_short_ratio with persistent state carry-forward.

## Known Deviations vs. Report Logic

- advance_decline now follows the mentor direction more closely, but the published report still does not expose a line-by-line official daily implementation; the current month-end YoY mapping is an approximation.
- option_iv uses daily equal-weight averaging across 50ETF / 300ETF / 500ETF before MA20 smoothing. This remains a practical reconstruction rather than a guaranteed report-identical weighting rule.
- ERP raw pe_ttm contains missing values; no aggressive filling or parameter tuning is applied.
