# Data Availability Confirmation

Archive/reference only. The current strategy pipeline uses only existing raw CSV files and does not redownload data.

## Confirmed Direction Items

- option_pcr uses the reciprocal `pcr_inverse = call_amount / put_amount` and a contrarian direction.
- option_iv uses the IV-skew composite and a contrarian direction.
- futures member ratio direction is confirmed by both the auxiliary report and RiceQuant documentation.

## Still Requires Manual Confirmation

- advance_decline daily trend transformation.
- option_iv cross-underlying weighting across 50ETF / 300ETF / 500ETF.
- ERP missing-value handling for pe_ttm.
