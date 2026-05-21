import json
from pathlib import Path

import pandas as pd

from utils import DEFAULT_OUTPUT_DIR


def csv_summary(path):
    path = Path(path)
    if not path.exists():
        return None
    rows = 0
    missing = {}
    columns = None
    min_date = None
    max_date = None
    for chunk in pd.read_csv(path, compression="gzip", chunksize=500000):
        if columns is None:
            columns = [str(c) for c in chunk.columns]
            missing = {str(c): 0 for c in chunk.columns}
        rows += len(chunk)
        for col in chunk.columns:
            missing[str(col)] += int(chunk[col].isna().sum())
        if "date" in chunk.columns and len(chunk):
            d = pd.to_datetime(chunk["date"], errors="coerce")
            if d.notna().any():
                cmin = d.min()
                cmax = d.max()
                min_date = cmin if min_date is None or cmin < min_date else min_date
                max_date = cmax if max_date is None or cmax > max_date else max_date
    ratios = {col: (missing[col] / rows if rows else None) for col in missing}
    return {
        "rows": rows,
        "columns": columns or [],
        "start_date": str(min_date.date()) if min_date is not None else "",
        "end_date": str(max_date.date()) if max_date is not None else "",
        "missing_ratio": ratios,
    }


def main():
    output_dir = Path(DEFAULT_OUTPUT_DIR)
    manifest_path = output_dir / "metadata" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []

    lines = ["# Data Dictionary", ""]
    for item in sorted(manifest, key=lambda x: x.get("name", "")):
        if not Path(item.get("file", "")).exists():
            continue
        summary = csv_summary(item.get("file", ""))
        if summary:
            item["rows"] = summary["rows"]
            item["start_date"] = summary["start_date"]
            item["end_date"] = summary["end_date"]
            item["missing_ratio"] = summary["missing_ratio"]
        lines.extend([
            f"## {item.get('name')}",
            "",
            f"- file: `{item.get('file')}`",
            f"- frequency: {item.get('frequency')}",
            f"- rows in summary/sample: {item.get('rows')}",
            f"- date range: {item.get('start_date')} to {item.get('end_date')}",
            f"- description: {item.get('description')}",
            "",
            "Fields:",
            "",
        ])
        fields = item.get("fields", {})
        for field, desc in fields.items():
            lines.append(f"- `{field}`: {desc}")
        lines.extend(["", "Missing ratio:", ""])
        for field, ratio in item.get("missing_ratio", {}).items():
            lines.append(f"- `{field}`: {ratio:.6f}" if isinstance(ratio, float) else f"- `{field}`: {ratio}")
        lines.extend(["", f"Notes: {item.get('notes')}", ""])
    Path("data_dictionary.md").write_text("\n".join(lines), encoding="utf-8")

    readme = """# A-share Timing Data Preparation

This stage downloads, cleans, saves, and checks raw data only. It does not run timing backtests, does not map positions, and does not evaluate strategy performance.

## Output format

All saved data files use compressed CSV: `*.csv.gz`.

## Interfaces and rules

- ERP: `rqdatac.index_indicator` for `000985.XSHG` `pe_ttm`, plus `rqdatac.get_yield_curve` for `10Y`.
- Margin buy: `rqdatac.get_securities_margin` stock-level `buy_on_margin_value`, aggregated by date.
- Bollinger input: `rqdatac.get_price` for `000985.XSHG` daily `close`.
- Advance/decline amount input: `rqdatac.get_price` for all CS instruments with `close`, `prev_close`, `total_turnover`; flat stocks enter `total_amount` only, newly listed stocks with missing `prev_close` enter `total_amount` only, ST stocks are not filtered, suspended rows are kept as returned.
- Option PCR: `rqdatac.all_instruments(type='Option')` for `option_type`, plus `rqdatac.get_price` for 50ETF option `volume`, `total_turnover`, `open_interest`.
- Option IV: `rqdatac.options.get_greeks` for `iv`, option instrument table for `strike_price`/`maturity_date`, and underlying ETF `close` as `underlying_price`. Near-month options are selected by earliest maturity date after each trading date. Nearest-neighbor and interpolation versions are both saved.
- Futures member: `rqdatac.futures.get_member_rank` with `rank_by='long'/'short'` for IF, plus IH/IC extension when available.

## Confirmed口径

- `000985.XSHG` is used as the Wind All-A proxy per stage-4 instruction.
- 50ETF option `option_type` exists in the option instrument table.
- Option `iv` exists through `rqdatac.options.get_greeks`.
- IF/IH/IC member rank data can be queried with `rank_by='long'/'short'`.

## Still需要人工确认

- Non-margin stock-date records are absent/None rather than explicit zero; aggregation treats available margin records as the source.
- Option `underlying_price` is joined from underlying ETF close because it is not directly returned by the option Greeks/property APIs.
- Futures member rank returns a generic `volume` field. The scripts rename it to `long_position` or `short_position` depending on `rank_by`, but the field meaning should be checked against CFFEX/RiceQuant documentation.
- The option IV high/low value-state selection rule is implemented for data preparation, but the exact report convention may differ.
"""
    Path("README.md").write_text(readme, encoding="utf-8")

    rule = """# IV Selection Rule

This file documents the rule implemented in `data_download/download_option_iv.py`.

1. Underlyings: `510050.XSHG`, `510300.XSHG`, `510500.XSHG`.
2. Contract universe: option contracts whose listing interval overlaps the requested date range.
3. `underlying_price`: the underlying ETF daily close from `rqdatac.get_price`; it is not returned directly by `rqdatac.options.get_greeks`.
4. `moneyness = strike_price / underlying_price`.
5. Near-month filter: for each date and underlying, keep contracts with positive `days_to_expiry`, then select the earliest `maturity_date`.
6. Nearest-neighbor version: for each target moneyness `105/95`, `110/90`, `120/80`, select the contract whose moneyness is closest to the target. The selected contracts are saved in `data/raw/option_iv_selected_daily.csv.gz`.
7. Interpolation version: average IV by moneyness for the same date/underlying/near-month group, then linearly interpolate IV at each target moneyness when the target is inside the observed moneyness range.
8. Ratio table: `iv_105_95`, `iv_110_90`, `iv_120_80` are nearest-neighbor ratios; `_interp` columns are interpolation ratios.

TODO: The report's exact convention for using call-only, put-only, or pooled option contracts is not stated. The current implementation pools available option types for data preparation and records the selected `option_type` in the selected-contract table.
"""
    Path("iv_selection_rule.md").write_text(rule, encoding="utf-8")
    print("wrote data_dictionary.md README.md iv_selection_rule.md")


if __name__ == "__main__":
    main()
