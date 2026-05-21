from pathlib import Path

import pandas as pd

from utils import ensure_dirs, init_rqdatac, normalize_date_column, parse_args, print_summary, register_dataset, reset_date_index, write_csv_gz, write_sample_markdown


def main():
    args = parse_args("2010-01-04")
    root = ensure_dirs(args.output_dir)
    rqdatac = init_rqdatac()

    pe = rqdatac.index_indicator(["000985.XSHG"], args.start_date, args.end_date, fields=["pe_ttm"])
    pe = reset_date_index(pe)
    pe = normalize_date_column(pe)
    pe = pe[["date", "pe_ttm"]]

    yc = rqdatac.get_yield_curve(args.start_date, args.end_date)
    yc = yc.reset_index().rename(columns={"trading_date": "date", "10Y": "treasury_10y_yield"})
    yc = normalize_date_column(yc)
    yc = yc[["date", "treasury_10y_yield"]]

    out = pd.merge(pe, yc, on="date", how="left").sort_values("date")
    path = root / "raw" / "erp_raw.csv.gz"
    write_csv_gz(out, path)
    print_summary("erp_raw", out)
    write_sample_markdown(out, root / "samples" / "erp_raw_head.md", "ERP Raw Head")
    register_dataset(
        args.output_dir,
        "ERP raw",
        path,
        out,
        "daily",
        "000985.XSHG PE_TTM and China treasury 10Y yield aligned by date; no ERP signal is calculated.",
        {
            "date": "calendar/trading date",
            "pe_ttm": "Index PE_TTM from rqdatac.index_indicator for 000985.XSHG",
            "treasury_10y_yield": "10Y yield from rqdatac.get_yield_curve",
        },
        "000985.XSHG is used as the Wind All-A proxy confirmed by the user request.",
    )


if __name__ == "__main__":
    main()
