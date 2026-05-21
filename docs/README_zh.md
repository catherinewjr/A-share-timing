# 华泰择时复现说明

## 当前状态

当前目录包含完整的策略复现流水线。`data/raw/` 下的原始 CSV 被视为固定输入，主流程不会修改这些文件。

## 项目结构

```text
data/raw -> 固定原始 CSV 输入
data/processed/signals -> 7 个单信号 CSV
data/processed/factors -> 因子合成 CSV
data/processed/backtest -> 回测日度结果 CSV
outputs/plots -> PNG 图表
outputs/tables -> performance 和 summary 表
outputs/logs -> pipeline_log.md
src/ -> 可复现源码
```

## 复现流程

1. 从 `data/raw/` 读取原始 CSV。
2. 计算 7 个单信号。
3. 合成为估值 / 资金 / 技术 / 情绪 / 左侧 / 右侧 / 最终信号。
4. 对 `000985.XSHG` 收盘价收益使用 `final_signal.shift(1)` 做回测。
5. 生成图表、结果表和日志。

## 运行命令

```bash
python main.py
```

## 本轮信号层修正

- 本轮按 mentor 文档把 7 个信号统一改成持续型信号。
- BOLL / 分位数信号现在只有在突破阈值时才切换状态，中间区域保持上一状态。
- PCR 改为倒数口径 + 反向布林带。
- IV 改为 MA20 平滑 + 反向布林带。
- 期货会员持仓改为正向布林带。
- 个股涨跌成交额占比差改为 MA60 平滑 + 月末同比方向 + 日频前向填充。

## 辅助研报

- 《A股择时之期权期货市场指标》（2024-07-14）
- 《A股择时之情绪面指标测试》（2021-02-04）
- 《A股择时之技术面指标测试》（2021-08-17）

## 核心输出

- `data/processed/signals/*.csv`
- `data/processed/factors/factors.csv`
- `data/processed/backtest/backtest.csv`
- `outputs/tables/performance.csv`
- `outputs/plots/*.png`

## 各信号缺失率

- `erp`：`raw_value` 缺失率 = 0.102929
- `margin_buy`：`raw_value` 缺失率 = 0.000000
- `bollinger`：`raw_value` 缺失率 = 0.000000
- `advance_decline`：`raw_value` 缺失率 = 0.015856
- `option_pcr`：`raw_value` 缺失率 = 0.000000
- `option_iv`：`raw_value` 缺失率 = 0.009586
- `futures_member`：`raw_value` 缺失率 = 0.000000

## 各信号实现说明

- `erp`：ERP = 1 / pe_ttm - treasury_10y_yield, mapped by a 1250-day rolling percentile in persistent trend mode.
- `margin_buy`：Use market-level margin_buy_total and map it with trend Bollinger. The state is held until the opposite breakout appears.
- `bollinger`：Use 000985.XSHG close and map it with trend Bollinger using window=20 and std=2.
- `advance_decline`：Use MA60-smoothed (up_amount - down_amount) / total_amount, convert to month-end values, compute monthly YoY direction, then forward-fill back to trading days.
- `option_pcr`：Use pcr_inverse = 1 / amount_pcr = call_amount / put_amount, then apply reverse Bollinger with persistent state carry-forward.
- `option_iv`：Use the mean of iv_105_95, iv_110_90, and iv_120_80, average across ETF underlyings by date, smooth with MA20, then apply reverse Bollinger with persistent state carry-forward.
- `futures_member`：Use IF only and apply trend Bollinger to long_short_ratio with persistent state carry-forward.

## 与研报口径可能存在的偏差

- advance_decline now follows the mentor direction more closely, but the published report still does not expose a line-by-line official daily implementation; the current month-end YoY mapping is an approximation.
- option_iv uses daily equal-weight averaging across 50ETF / 300ETF / 500ETF before MA20 smoothing. This remains a practical reconstruction rather than a guaranteed report-identical weighting rule.
- ERP raw pe_ttm contains missing values; no aggressive filling or parameter tuning is applied.
