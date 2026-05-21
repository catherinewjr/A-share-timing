# 数据可得性确认

归档 / 参考用途。当前策略流水线只使用现有 raw CSV，不重新下载数据。

## 已确认的方向口径

- option_pcr 使用倒数口径 `pcr_inverse = call_amount / put_amount`，并按反向策略映射。
- option_iv 使用 IV 曲线组合，并按反向策略映射。
- 期货会员持仓方向已由辅助研报与 RiceQuant 文档共同确认。

## 仍需人工确认的问题

- advance_decline 的日频趋势映射方式。
- option_iv 在 50ETF / 300ETF / 500ETF 之间的聚合权重。
- ERP 中 pe_ttm 缺失值的处理方式。
