# IV Selection Rule

Archive/reference only. The raw-data layer already contains prepared ratio files.

- Main signal input: `data/raw/option_iv_ratio_daily.csv`.
- Signal raw value: mean of `iv_105_95`, `iv_110_90`, and `iv_120_80`.
- If multiple underlyings are present on a date, aggregate by daily mean before mapping.
- Direction confirmed from the auxiliary report: high IV-skew composite -> -1, low composite -> +1.
