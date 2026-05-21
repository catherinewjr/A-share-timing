import numpy as np
import pandas as pd

from utils import chunks, ensure_dirs, init_rqdatac, normalize_date_column, parse_args, print_summary, register_dataset, reset_date_index, write_csv_gz, write_sample_markdown


UNDERLYINGS = ["510050.XSHG", "510300.XSHG", "510500.XSHG"]
TARGET_PAIRS = [(1.05, 0.95), (1.10, 0.90), (1.20, 0.80)]


def nearest_month_group(day_df):
    day_df = day_df[day_df["days_to_expiry"] > 0].copy()
    if day_df.empty:
        return day_df
    nearest_expiry = day_df["maturity_date_dt"].min()
    return day_df[day_df["maturity_date_dt"].eq(nearest_expiry)].copy()


def select_nearest(day_df, target):
    if day_df.empty:
        return None
    tmp = day_df.copy()
    tmp["distance"] = (tmp["moneyness"] - target).abs()
    tmp = tmp.sort_values(["distance", "days_to_expiry", "contract"])
    return tmp.iloc[0]


def interpolate_iv(day_df, target):
    tmp = day_df.dropna(subset=["moneyness", "implied_volatility"]).copy()
    if len(tmp) < 2:
        return np.nan
    curve = tmp.groupby("moneyness", as_index=False)["implied_volatility"].mean().sort_values("moneyness")
    x = curve["moneyness"].to_numpy(dtype=float)
    y = curve["implied_volatility"].to_numpy(dtype=float)
    if target < x.min() or target > x.max():
        return np.nan
    return float(np.interp(target, x, y))


def main():
    args = parse_args("2017-03-06")
    root = ensure_dirs(args.output_dir)
    rqdatac = init_rqdatac()
    raw_path = root / "raw" / "option_iv_contract_raw.csv.gz"
    selected_path = root / "raw" / "option_iv_selected_daily.csv.gz"
    ratio_path = root / "raw" / "option_iv_ratio_daily.csv.gz"
    if raw_path.exists():
        raw_path.unlink()

    inst_all = rqdatac.all_instruments(type="Option")
    start = pd.to_datetime(args.start_date)
    end = pd.to_datetime(args.end_date)
    raw_parts_for_selection = []

    for underlying in UNDERLYINGS:
        inst = inst_all[inst_all["underlying_order_book_id"].eq(underlying)].copy()
        inst["listed_date_dt"] = pd.to_datetime(inst["listed_date"], errors="coerce")
        inst["de_listed_date_dt"] = pd.to_datetime(inst["de_listed_date"], errors="coerce")
        inst = inst[(inst["listed_date_dt"] <= end) & (inst["de_listed_date_dt"] >= start)]
        if inst.empty:
            print(f"no option contracts for {underlying}")
            continue
        static = inst[["order_book_id", "underlying_order_book_id", "option_type", "strike_price", "listed_date", "maturity_date", "de_listed_date"]].rename(columns={"order_book_id": "contract"})

        underlying_price = rqdatac.get_price(underlying, args.start_date, args.end_date, fields=["close"], expect_df=True)
        underlying_price = reset_date_index(underlying_price)
        underlying_price = normalize_date_column(underlying_price)
        underlying_price = underlying_price.rename(columns={"close": "underlying_price"})
        underlying_price = underlying_price[["date", "underlying_price"]]

        for i, batch in enumerate(chunks(inst["order_book_id"].tolist(), 250), start=1):
            try:
                greeks = rqdatac.options.get_greeks(batch, args.start_date, args.end_date, fields=["iv"])
            except Exception as exc:
                print(f"option IV batch {underlying} {i} failed: {type(exc).__name__}: {exc}")
                continue
            if greeks is None or len(greeks) == 0:
                continue
            out = reset_date_index(greeks)
            out = normalize_date_column(out)
            out = out.rename(columns={"order_book_id": "contract", "iv": "implied_volatility"})
            out = out.merge(static, on="contract", how="left")
            out = out.merge(underlying_price, on="date", how="left")
            out["maturity_date_dt"] = pd.to_datetime(out["maturity_date"], errors="coerce")
            out["date_dt"] = pd.to_datetime(out["date"], errors="coerce")
            out["days_to_expiry"] = (out["maturity_date_dt"] - out["date_dt"]).dt.days
            out["moneyness"] = out["strike_price"] / out["underlying_price"]
            out = out[[
                "date", "contract", "underlying_order_book_id", "option_type", "strike_price",
                "underlying_price", "maturity_date", "days_to_expiry", "moneyness", "implied_volatility",
                "listed_date", "de_listed_date",
            ]]
            write_csv_gz(out, raw_path, mode="a" if raw_path.exists() else "w", header=not raw_path.exists())
            raw_parts_for_selection.append(out)
            print(f"option IV batch {underlying} {i}: {out.shape}")

    if raw_parts_for_selection:
        raw = pd.concat(raw_parts_for_selection, ignore_index=True)
    else:
        raw = pd.DataFrame(columns=["date", "contract", "underlying_order_book_id", "option_type", "strike_price", "underlying_price", "maturity_date", "days_to_expiry", "moneyness", "implied_volatility"])
    raw["maturity_date_dt"] = pd.to_datetime(raw.get("maturity_date"), errors="coerce")

    selected_rows = []
    ratio_rows = []
    for (underlying, date), day in raw.groupby(["underlying_order_book_id", "date"]):
        near = nearest_month_group(day)
        ratio_row = {"date": date, "underlying": underlying}
        for high, low in TARGET_PAIRS:
            high_sel = select_nearest(near, high)
            low_sel = select_nearest(near, low)
            label = f"{int(high*100)}_{int(low*100)}"
            if high_sel is not None:
                selected_rows.append({**high_sel.to_dict(), "target_moneyness": high, "pair": label, "side": "high", "selection_method": "nearest"})
            if low_sel is not None:
                selected_rows.append({**low_sel.to_dict(), "target_moneyness": low, "pair": label, "side": "low", "selection_method": "nearest"})
            if high_sel is not None and low_sel is not None and low_sel["implied_volatility"] != 0:
                ratio_row[f"iv_{label}_nearest"] = high_sel["implied_volatility"] / low_sel["implied_volatility"]
            else:
                ratio_row[f"iv_{label}_nearest"] = np.nan
            high_interp = interpolate_iv(near, high)
            low_interp = interpolate_iv(near, low)
            if pd.notna(high_interp) and pd.notna(low_interp) and low_interp != 0:
                ratio_row[f"iv_{label}_interp"] = high_interp / low_interp
            else:
                ratio_row[f"iv_{label}_interp"] = np.nan
        ratio_rows.append(ratio_row)

    selected = pd.DataFrame(selected_rows)
    if "maturity_date_dt" in selected.columns:
        selected = selected.drop(columns=["maturity_date_dt"], errors="ignore")
    ratio = pd.DataFrame(ratio_rows).sort_values(["underlying", "date"]) if ratio_rows else pd.DataFrame()
    # Primary 50ETF-friendly aliases requested by the user. These keep the nearest-neighbor version explicit.
    for label in ["105_95", "110_90", "120_80"]:
        col = f"iv_{label}_nearest"
        if col in ratio.columns:
            ratio[f"iv_{label}"] = ratio[col]

    write_csv_gz(selected, selected_path)
    write_csv_gz(ratio, ratio_path)
    print_summary("option_iv_selected_daily", selected)
    print_summary("option_iv_ratio_daily", ratio)
    write_sample_markdown(selected, root / "samples" / "option_iv_selected_daily_head.md", "Option IV Selected Daily Head")
    write_sample_markdown(ratio, root / "samples" / "option_iv_ratio_daily_head.md", "Option IV Ratio Daily Head")
    raw_sample = pd.read_csv(raw_path, compression="gzip", nrows=1000) if raw_path.exists() else pd.DataFrame()
    write_sample_markdown(raw_sample, root / "samples" / "option_iv_contract_raw_head.md", "Option IV Contract Raw Head")

    register_dataset(
        args.output_dir,
        "Option IV contract raw",
        raw_path,
        raw_sample,
        "daily contract-level",
        "Contract-level option IV for 50ETF, 300ETF and 500ETF option candidates, plus underlying ETF close as underlying_price.",
        {"date": "trading date", "contract": "option order_book_id", "underlying_price": "underlying ETF close from rqdatac.get_price", "implied_volatility": "iv from rqdatac.options.get_greeks"},
        "underlying_price is not returned by options.get_greeks; it is joined from the underlying ETF close.",
    )
    register_dataset(
        args.output_dir,
        "Option IV selected daily",
        selected_path,
        selected,
        "daily selected contracts",
        "Nearest-month and nearest-moneyness selected contracts for 105/95, 110/90 and 120/80 pairs.",
        {"target_moneyness": "target strike/underlying_price", "selection_method": "nearest", "pair": "high/low moneyness pair"},
        "Nearest-neighbor selection is implemented. Interpolation is saved in the ratio table.",
    )
    register_dataset(
        args.output_dir,
        "Option IV ratio daily",
        ratio_path,
        ratio,
        "daily",
        "Prepared IV high/low ratio table using nearest-neighbor and interpolation versions.",
        {"iv_105_95": "nearest-neighbor 1.05 / 0.95 IV ratio", "iv_105_95_interp": "linear interpolation version"},
        "This is a prepared data ratio, not a final timing signal.",
    )


if __name__ == "__main__":
    main()
