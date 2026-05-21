import pandas as pd

from utils import chunks, ensure_dirs, init_rqdatac, normalize_date_column, parse_args, print_summary, register_dataset, reset_date_index, write_csv_gz, write_sample_markdown


def main():
    args = parse_args("2017-03-06")
    root = ensure_dirs(args.output_dir)
    rqdatac = init_rqdatac()
    raw_path = root / "raw" / "option_50etf_contract_raw.csv.gz"
    agg_path = root / "raw" / "option_50etf_pcr_daily.csv.gz"
    if raw_path.exists():
        raw_path.unlink()

    inst = rqdatac.all_instruments(type="Option")
    inst = inst[inst["underlying_order_book_id"].eq("510050.XSHG")].copy()
    inst["listed_date_dt"] = pd.to_datetime(inst["listed_date"], errors="coerce")
    inst["de_listed_date_dt"] = pd.to_datetime(inst["de_listed_date"], errors="coerce")
    start = pd.to_datetime(args.start_date)
    end = pd.to_datetime(args.end_date)
    inst = inst[(inst["listed_date_dt"] <= end) & (inst["de_listed_date_dt"] >= start)]
    ids = inst["order_book_id"].tolist()
    static = inst[["order_book_id", "option_type", "strike_price", "listed_date", "maturity_date", "de_listed_date"]]

    daily_parts = []
    for i, batch in enumerate(chunks(ids, 250), start=1):
        try:
            df = rqdatac.get_price(
                batch,
                args.start_date,
                args.end_date,
                fields=["volume", "total_turnover", "open_interest"],
                expect_df=True,
            )
        except Exception as exc:
            print(f"50ETF option PCR batch {i} failed: {type(exc).__name__}: {exc}")
            continue
        if df is None or len(df) == 0:
            continue
        out = reset_date_index(df)
        out = normalize_date_column(out)
        out = out.rename(columns={"order_book_id": "contract", "total_turnover": "amount", "open_interest": "oi"})
        out = out.merge(static.rename(columns={"order_book_id": "contract"}), on="contract", how="left")
        out = out[["date", "contract", "option_type", "volume", "amount", "oi", "strike_price", "listed_date", "maturity_date", "de_listed_date"]]
        write_csv_gz(out, raw_path, mode="a" if raw_path.exists() else "w", header=not raw_path.exists())

        g = out.groupby(["date", "option_type"], as_index=False).agg(
            volume=("volume", "sum"),
            amount=("amount", "sum"),
            oi=("oi", "sum"),
        )
        daily_parts.append(g)
        print(f"50ETF option PCR batch {i}: {out.shape}")

    if daily_parts:
        daily = pd.concat(daily_parts, ignore_index=True).groupby(["date", "option_type"], as_index=False).sum()
        pivot = daily.pivot(index="date", columns="option_type", values=["volume", "amount", "oi"]).fillna(0.0)
        out = pd.DataFrame({"date": pivot.index})
        for base, cname in [("volume", "volume"), ("amount", "amount"), ("oi", "oi")]:
            out[f"call_{cname}"] = pivot[(base, "C")].to_numpy() if (base, "C") in pivot.columns else 0.0
            out[f"put_{cname}"] = pivot[(base, "P")].to_numpy() if (base, "P") in pivot.columns else 0.0
        out["volume_pcr"] = out["put_volume"] / out["call_volume"].replace(0, pd.NA)
        out["amount_pcr"] = out["put_amount"] / out["call_amount"].replace(0, pd.NA)
        out["oi_pcr"] = out["put_oi"] / out["call_oi"].replace(0, pd.NA)
        out = out[["date", "put_volume", "call_volume", "put_amount", "call_amount", "put_oi", "call_oi", "volume_pcr", "amount_pcr", "oi_pcr"]]
    else:
        out = pd.DataFrame(columns=["date", "put_volume", "call_volume", "put_amount", "call_amount", "put_oi", "call_oi", "volume_pcr", "amount_pcr", "oi_pcr"])
    out = out.sort_values("date")
    write_csv_gz(out, agg_path)
    print_summary("option_50etf_pcr_daily", out)
    write_sample_markdown(out, root / "samples" / "option_50etf_pcr_daily_head.md", "50ETF Option PCR Daily Head")
    raw_sample = pd.read_csv(raw_path, compression="gzip", nrows=1000) if raw_path.exists() else pd.DataFrame()
    write_sample_markdown(raw_sample, root / "samples" / "option_50etf_contract_raw_head.md", "50ETF Option Contract Raw Head")

    register_dataset(
        args.output_dir,
        "50ETF option contract raw",
        raw_path,
        raw_sample,
        "daily contract-level",
        "Contract-level 50ETF option volume, amount and open interest.",
        {"date": "trading date", "contract": "option order_book_id", "option_type": "C/P from instrument table", "volume": "contract trading volume", "amount": "total_turnover", "oi": "open_interest"},
        "Only 510050.XSHG options are included for PCR.",
    )
    register_dataset(
        args.output_dir,
        "50ETF option PCR daily",
        agg_path,
        out,
        "daily",
        "Daily aggregated put/call volume, amount, and open interest ratios for 50ETF options.",
        {"date": "trading date", "volume_pcr": "put_volume / call_volume", "amount_pcr": "put_amount / call_amount", "oi_pcr": "put_oi / call_oi"},
        "PCR ratios are prepared data series, not final timing signals.",
    )


if __name__ == "__main__":
    main()
