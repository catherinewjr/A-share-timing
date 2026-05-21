from pathlib import Path

from utils import ensure_dirs, init_rqdatac, normalize_date_column, parse_args, print_summary, register_dataset, reset_date_index, write_csv_gz, write_sample_markdown


def main():
    args = parse_args("2010-01-04")
    root = ensure_dirs(args.output_dir)
    rqdatac = init_rqdatac()

    df = rqdatac.get_price("000985.XSHG", args.start_date, args.end_date, fields=["close"], expect_df=True)
    out = reset_date_index(df)
    out = normalize_date_column(out)
    out = out[["date", "close"]]
    path = root / "raw" / "bollinger_price_raw.csv.gz"
    write_csv_gz(out, path)
    print_summary("bollinger_price_raw", out)
    write_sample_markdown(out, root / "samples" / "bollinger_price_raw_head.md", "Bollinger Price Raw Head")
    register_dataset(
        args.output_dir,
        "Bollinger price raw",
        path,
        out,
        "daily",
        "000985.XSHG daily close for later Bollinger-band calculation. No band or signal is calculated.",
        {"date": "trading date", "close": "daily close of 000985.XSHG"},
        "Bollinger parameters are not applied in this stage.",
    )


if __name__ == "__main__":
    main()
