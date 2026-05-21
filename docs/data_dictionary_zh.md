# 数据字典

归档 / 参考用途。本文档记录当前复现流水线使用的 raw CSV 文件。

## erp_raw.csv

- 说明：ERP input: date, pe_ttm, treasury_10y_yield
- 字段：date, pe_ttm, treasury_10y_yield
- 行数：3721
- 起始日期：2010-01-04
- 结束日期：2025-04-30
- 缺失率：{'date': 0.0, 'pe_ttm': 0.10292932007524859, 'treasury_10y_yield': 0.0}

## margin_buy_total.csv

- 说明：Margin-buy input: date, margin_buy_total
- 字段：date, margin_buy_total
- 行数：3625
- 起始日期：2010-05-27
- 结束日期：2025-04-30
- 缺失率：{'date': 0.0, 'margin_buy_total': 0.0}

## bollinger_price_raw.csv

- 说明：Price input for Bollinger and backtest asset returns
- 字段：date, close
- 行数：3721
- 起始日期：2010-01-04
- 结束日期：2025-04-30
- 缺失率：{'date': 0.0, 'close': 0.0}

## advance_decline_amount_daily.csv

- 说明：Advance/decline input: up_amount, down_amount, total_amount
- 字段：date, up_amount, down_amount, total_amount
- 行数：3721
- 起始日期：2010-01-04
- 结束日期：2025-04-30
- 缺失率：{'date': 0.0, 'up_amount': 0.0, 'down_amount': 0.0, 'total_amount': 0.0}

## option_50etf_pcr_daily.csv

- 说明：PCR input: put/call volume, amount, open interest and PCR ratios
- 字段：date, put_volume, call_volume, put_amount, call_amount, put_oi, call_oi, volume_pcr, amount_pcr, oi_pcr
- 行数：1982
- 起始日期：2017-03-06
- 结束日期：2025-04-30
- 缺失率：{'date': 0.0, 'put_volume': 0.0, 'call_volume': 0.0, 'put_amount': 0.0, 'call_amount': 0.0, 'put_oi': 0.0, 'call_oi': 0.0, 'volume_pcr': 0.0, 'amount_pcr': 0.0, 'oi_pcr': 0.0}

## option_iv_ratio_daily.csv

- 说明：IV ratio input: daily 105/95, 110/90, 120/80 ratios
- 字段：date, underlying, iv_105_95_nearest, iv_105_95_interp, iv_110_90_nearest, iv_110_90_interp, iv_120_80_nearest, iv_120_80_interp, iv_105_95, iv_110_90, iv_120_80
- 行数：3911
- 起始日期：2017-03-06
- 结束日期：2025-04-30
- 缺失率：{'date': 0.0, 'underlying': 0.0, 'iv_105_95_nearest': 0.0, 'iv_105_95_interp': 0.3681922781897213, 'iv_110_90_nearest': 0.0, 'iv_110_90_interp': 0.6384556379442597, 'iv_120_80_nearest': 0.0, 'iv_120_80_interp': 0.9209920736384556, 'iv_105_95': 0.0, 'iv_110_90': 0.0, 'iv_120_80': 0.0}

## futures_member_long_short_daily.csv

- 说明：Futures member input: IF/IH/IC daily long/short top20 summaries
- 字段：date, underlying, long_sum_top20, short_sum_top20, long_short_ratio
- 行数：5946
- 起始日期：2017-03-06
- 结束日期：2025-04-30
- 缺失率：{'date': 0.0, 'underlying': 0.0, 'long_sum_top20': 0.0, 'short_sum_top20': 0.0, 'long_short_ratio': 0.0}

