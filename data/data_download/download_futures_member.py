import pandas as pd

from utils import ensure_dirs, init_rqdatac, parse_args, print_summary, register_dataset, write_csv_gz, write_sample_markdown


UNDERLYINGS = ["IF", "IH", "IC"]


def get_rank(rqdatac, underlying, date, rank_by):
    df = rqdatac.futures.get_member_rank(underlying, trading_date=date, rank_by=rank_by)
    if df is None or len(df) == 0:
        return pd.DataFrame()
    out = df.reset_index().rename(columns={"trading_date": "date", "volume": f"{rank_by}_position"})
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out["underlying"] = underlying
    return out[["date", "underlying", "commodity_id", "rank", "member_name", f"{rank_by}_position", "volume_change"]]


def main():
    args = parse_args("2017-03-06")
    root = ensure_dirs(args.output_dir)
    rqdatac = init_rqdatac()
    raw_path = root / "raw" / "futures_member_rank_raw.csv.gz"
    agg_path = root / "raw" / "futures_member_long_short_daily.csv.gz"
    if raw_path.exists():
        raw_path.unlink()

    dates = rqdatac.get_trading_dates(args.start_date, args.end_date)
    raw_parts = []
    agg_rows = []
    for underlying in UNDERLYINGS:
        for idx, d in enumerate(dates, start=1):
            date = str(d)
            try:
                long_df = get_rank(rqdatac, underlying, date, "long")
                short_df = get_rank(rqdatac, underlying, date, "short")
            except Exception as exc:
                print(f"member rank {underlying} {date} failed: {type(exc).__name__}: {exc}")
                continue
            if long_df.empty or short_df.empty:
                continue
            long_top = long_df[long_df["rank"] <= 20].copy()
            short_top = short_df[short_df["rank"] <= 20].copy()
            long_top = long_top.rename(columns={"volume_change": "long_position_change"})
            short_top = short_top.rename(columns={"volume_change": "short_position_change"})

            merged = pd.merge(
                long_top,
                short_top[["date", "underlying", "rank", "member_name", "short_position", "short_position_change"]],
                on=["date", "underlying", "rank", "member_name"],
                how="outer",
            )
            write_csv_gz(merged, raw_path, mode="a" if raw_path.exists() else "w", header=not raw_path.exists())
            raw_parts.append(merged.head(0))
            long_sum = pd.to_numeric(long_top["long_position"], errors="coerce").sum()
            short_sum = pd.to_numeric(short_top["short_position"], errors="coerce").sum()
            agg_rows.append({
                "date": date,
                "underlying": underlying,
                "long_sum_top20": long_sum,
                "short_sum_top20": short_sum,
                "long_short_ratio": long_sum / short_sum if short_sum else pd.NA,
            })
            if idx % 100 == 0:
                print(f"member rank {underlying}: processed {idx}/{len(dates)} dates")

    agg = pd.DataFrame(agg_rows).sort_values(["underlying", "date"]) if agg_rows else pd.DataFrame(columns=["date", "underlying", "long_sum_top20", "short_sum_top20", "long_short_ratio"])
    write_csv_gz(agg, agg_path)
    print_summary("futures_member_long_short_daily", agg)
    write_sample_markdown(agg, root / "samples" / "futures_member_long_short_daily_head.md", "Futures Member Long Short Daily Head")
    raw_sample = pd.read_csv(raw_path, compression="gzip", nrows=1000) if raw_path.exists() else pd.DataFrame()
    write_sample_markdown(raw_sample, root / "samples" / "futures_member_rank_raw_head.md", "Futures Member Rank Raw Head")
    notes = (
        "rqdatac.futures.get_member_rank returns a generic column named volume. "
        "This script calls rank_by='long' and rank_by='short' and renames returned volume to long_position/short_position. "
        "This field meaning still needs manual confirmation against CFFEX wording."
    )
    register_dataset(
        args.output_dir,
        "Futures member rank raw",
        raw_path,
        raw_sample,
        "daily member-level",
        "Top-20 member rank raw data for IF and extension underlyings IH/IC when available.",
        {"date": "trading date", "underlying": "IF/IH/IC", "member_name": "member name", "long_position": "volume returned under rank_by='long'", "short_position": "volume returned under rank_by='short'", "rank": "member rank"},
        notes,
    )
    register_dataset(
        args.output_dir,
        "Futures member long short daily",
        agg_path,
        agg,
        "daily",
        "Daily top-20 long and short member position sums and long/short ratio for IF/IH/IC.",
        {"date": "trading date", "long_sum_top20": "sum of top-20 long_position", "short_sum_top20": "sum of top-20 short_position", "long_short_ratio": "long_sum_top20 / short_sum_top20"},
        notes,
    )


if __name__ == "__main__":
    main()
