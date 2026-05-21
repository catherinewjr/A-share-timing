# Pipeline Log

- run_time: 2026-05-21T14:26:16
- project_root: /Users/swiftcatherine/local_code/projects/huatai_timing
- end_date: 2025-04-30
- input_files:
  - data/raw/erp_raw.csv
  - data/raw/margin_buy_total.csv
  - data/raw/bollinger_price_raw.csv
  - data/raw/advance_decline_amount_daily.csv
  - data/raw/option_50etf_pcr_daily.csv
  - data/raw/option_iv_ratio_daily.csv
  - data/raw/futures_member_long_short_daily.csv
- output_files:
  - data/processed/signals/*.csv
  - data/processed/factors/factors.csv
  - data/processed/backtest/backtest.csv
  - outputs/tables/performance.csv
  - outputs/plots/*.png
- backtest_start_date: 2010-01-04
- backtest_end_date: 2025-04-30
- used_shift_1: True

## Mentor-Document Signal Update

- Persistent-state signal logic is now used throughout the signal layer.
- PCR uses reciprocal + reverse Bollinger.
- IV uses MA20 + reverse Bollinger.
- Futures member positioning uses trend Bollinger.
- Advance/decline uses MA60 + month-end YoY direction + forward-fill back to daily dates.

## Signal Date Ranges / Missing Ratios

- erp: 2010-01-04 -> 2025-04-30, raw_value_missing=0.102929
- margin_buy: 2010-05-27 -> 2025-04-30, raw_value_missing=0.000000
- bollinger: 2010-01-04 -> 2025-04-30, raw_value_missing=0.000000
- advance_decline: 2010-01-04 -> 2025-04-30, raw_value_missing=0.015856
- option_pcr: 2017-03-06 -> 2025-04-30, raw_value_missing=0.000000
- option_iv: 2017-03-06 -> 2025-04-30, raw_value_missing=0.009586
- futures_member: 2017-03-06 -> 2025-04-30, raw_value_missing=0.000000

## Still Requires Manual Confirmation

- advance_decline monthly YoY transformation is still an approximation because the target report does not publish a fully explicit daily formula.
- option_iv daily aggregation across 50ETF / 300ETF / 500ETF remains a practical reconstruction, not a guaranteed report-identical weighting rule.
- ERP raw pe_ttm contains missing values and is not aggressively filled.
