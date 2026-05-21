from pathlib import Path

import pandas as pd

from utils import chunks, ensure_dirs, get_active_cs_universe, init_rqdatac, normalize_date_column, parse_args, print_summary, register_dataset, reset_date_index, write_csv_gz, write_sample_markdown


def main():
    args = parse_args("2010-01-04")
    root = ensure_dirs(args.output_dir)
    rqdatac = init_rqdatac()
    symbols = get_active_cs_universe(rqdatac, args.end_date)
    raw_path = root / "raw" / "ashare_daily_raw.csv.gz"
    agg_path = root / "raw" / "advance_decline_amount_daily.csv.gz"
    if raw_path.exists():
        raw_path.unlink()

    daily_parts = []
    for i, batch in enumerate(chunks(symbols, 200), start=1):
        try:
            df = rqdatac.get_price(
                batch,
                args.start_date,
                args.end_date,
                fields=["close", "prev_close", "total_turnover"],
                expect_df=True,
            )
        except Exception as exc:
            print(f"ashare daily batch {i} failed: {type(exc).__name__}: {exc}")
            continue
        if df is None or len(df) == 0:
            continue
        out = reset_date_index(df)
        out = normalize_date_column(out)
        out = out.rename(columns={"order_book_id": "stock", "total_turnover": "amount"})
        out = out[["date", "stock", "close", "prev_close", "amount"]]
        write_csv_gz(out, raw_path, mode="a" if raw_path.exists() else "w", header=not raw_path.exists())

        tmp = out.copy()
        tmp["amount"] = pd.to_numeric(tmp["amount"], errors="coerce")
        tmp["close"] = pd.to_numeric(tmp["close"], errors="coerce")
        tmp["prev_close"] = pd.to_numeric(tmp["prev_close"], errors="coerce")
        tmp["up_amount"] = tmp["amount"].where(tmp["close"] > tmp["prev_close"], 0.0)
        tmp["down_amount"] = tmp["amount"].where(tmp["close"] < tmp["prev_close"], 0.0)
        daily_parts.append(
            tmp.groupby("date", as_index=False).agg(
                up_amount=("up_amount", "sum"),
                down_amount=("down_amount", "sum"),
                total_amount=("amount", "sum"),
            )
        )
        print(f"ashare daily batch {i}: {out.shape}")

    if daily_parts:
        agg = pd.concat(daily_parts, ignore_index=True).groupby("date", as_index=False).sum()
    else:
        agg = pd.DataFrame(columns=["date", "up_amount", "down_amount", "total_amount"])
    agg = agg.sort_values("date")
    write_csv_gz(agg, agg_path)
    print_summary("advance_decline_amount_daily", agg)
    write_sample_markdown(agg, root / "samples" / "advance_decline_amount_daily_head.md", "Advance Decline Amount Daily Head")
    if raw_path.exists():
        raw_sample = pd.read_csv(raw_path, compression="gzip", nrows=1000)
    else:
        raw_sample = pd.DataFrame()
    write_sample_markdown(raw_sample, root / "samples" / "ashare_daily_raw_head.md", "A-share Daily Raw Head")

    common_notes = (
        "Flat stocks are included in total_amount but not up_amount/down_amount. "
        "Newly listed stocks with missing prev_close are included in total_amount if amount is available, but not up/down. "
        "ST stocks are not filtered. Suspended rows are kept as returned by rqdatac; missing amount is ignored by pandas sum."
    )
    register_dataset(
        args.output_dir,
        "A-share daily raw",
        raw_path,
        raw_sample,
        "daily stock-level",
        "Stock-level A-share close, prev_close, and amount for later advance/decline amount calculations.",
        {"date": "trading date", "stock": "A-share order_book_id", "close": "daily close", "prev_close": "previous close returned by rqdatac", "amount": "total_turnover from rqdatac.get_price"},
        common_notes,
    )
    register_dataset(
        args.output_dir,
        "Advance decline amount daily",
        agg_path,
        agg,
        "daily",
        "Prepared daily aggregate table with up_amount, down_amount and total_amount. This is an intermediate data table, not a timing signal.",
        {"date": "trading date", "up_amount": "sum of amount where close > prev_close", "down_amount": "sum of amount where close < prev_close", "total_amount": "sum of amount across returned stock rows"},
        common_notes,
    )


if __name__ == "__main__":
    main()
