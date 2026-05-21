import pandas as pd

from utils import ensure_dirs, init_rqdatac, normalize_date_column, parse_args, print_summary, register_dataset, reset_date_index, write_csv_gz, write_sample_markdown


MARKETS = ["XSHE", "XSHG"]


def main():
    args = parse_args("2010-05-27")
    root = ensure_dirs(args.output_dir)
    rqdatac = init_rqdatac()

    df = rqdatac.get_securities_margin(
        MARKETS,
        args.start_date,
        args.end_date,
        fields=["buy_on_margin_value"],
        expect_df=True,
    )

    market_raw = reset_date_index(df)
    market_raw = normalize_date_column(market_raw)
    market_raw = market_raw.rename(columns={"order_book_id": "market"})
    market_raw = market_raw[["date", "market", "buy_on_margin_value"]].sort_values(["date", "market"])

    total = (
        market_raw.groupby("date", as_index=False)["buy_on_margin_value"]
        .sum()
        .rename(columns={"buy_on_margin_value": "margin_buy_total"})
        .sort_values("date")
    )

    raw_path = root / "raw" / "margin_buy_market_raw.csv.gz"
    total_path = root / "raw" / "margin_buy_total.csv.gz"
    write_csv_gz(market_raw, raw_path)
    write_csv_gz(total, total_path)

    print_summary("margin_buy_market_raw", market_raw)
    print_summary("margin_buy_total", total)
    write_sample_markdown(market_raw, root / "samples" / "margin_buy_market_raw_head.md", "Margin Buy Market Raw Head")
    write_sample_markdown(total, root / "samples" / "margin_buy_total_head.md", "Margin Buy Total Head")

    register_dataset(
        args.output_dir,
        "Margin buy market raw",
        raw_path,
        market_raw,
        "daily market-level",
        "Market-level buy_on_margin_value for XSHE and XSHG returned directly by rqdatac.get_securities_margin.",
        {
            "date": "trading date",
            "market": "XSHE or XSHG",
            "buy_on_margin_value": "market-level margin buying value",
        },
        "This version follows the report requirement more closely than stock-level aggregation.",
    )
    register_dataset(
        args.output_dir,
        "Margin buy total",
        total_path,
        total,
        "daily",
        "Daily all-market margin buying value aggregated from the two market-level rows XSHE and XSHG.",
        {
            "date": "trading date",
            "margin_buy_total": "XSHE buy_on_margin_value + XSHG buy_on_margin_value",
        },
        "Downloaded directly at market level from RiceQuant, then summed across the two exchanges.",
    )


if __name__ == "__main__":
    main()
