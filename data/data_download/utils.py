import argparse
import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_END_DATE = "2025-04-30"
DEFAULT_OUTPUT_DIR = "data"


def parse_args(default_start):
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default=default_start)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def init_rqdatac():
    import rqdatac
    from rq_auth import RQ_PASSWORD, RQ_USERNAME

    rqdatac.init(RQ_USERNAME, RQ_PASSWORD)
    return rqdatac


def ensure_dirs(output_dir):
    root = Path(output_dir)
    for sub in ["raw", "samples", "metadata"]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def reset_date_index(df):
    if df is None:
        return pd.DataFrame()
    out = df.reset_index()
    rename = {}
    for col in out.columns:
        if col in ("date", "trade_date", "trading_date"):
            rename[col] = "date"
    out = out.rename(columns=rename)
    return out


def normalize_date_column(df):
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


def write_csv_gz(df, path, mode="w", header=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig", compression="gzip", mode=mode, header=header)


def append_csv_gz(df, path):
    path = Path(path)
    write_csv_gz(df, path, mode="a" if path.exists() else "w", header=not path.exists())


def summarize_df(df, date_col="date"):
    if df is None or len(df) == 0:
        return {
            "rows": 0,
            "columns": [],
            "start_date": "",
            "end_date": "",
            "missing_ratio": {},
        }
    summary = {
        "rows": int(len(df)),
        "columns": [str(c) for c in df.columns],
        "start_date": "",
        "end_date": "",
        "missing_ratio": {},
    }
    if date_col in df.columns:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        if dates.notna().any():
            summary["start_date"] = str(dates.min().date())
            summary["end_date"] = str(dates.max().date())
    for col in df.columns:
        summary["missing_ratio"][str(col)] = float(df[col].isna().mean())
    return summary


def print_summary(name, df):
    summary = summarize_df(df)
    print(f"{name}: shape={df.shape}")
    print(f"{name}: date_range={summary['start_date']}~{summary['end_date']}")
    print(f"{name}: missing_ratio={summary['missing_ratio']}")


def write_sample_markdown(df, path, title):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sample = df.head(20) if df is not None else pd.DataFrame()
    text = f"# {title}\n\n"
    text += f"- shape: {getattr(df, 'shape', '')}\n"
    summary = summarize_df(df)
    text += f"- date_range: {summary['start_date']} to {summary['end_date']}\n\n"
    text += "```csv\n"
    text += sample.to_csv(index=False)
    text += "```\n"
    path.write_text(text, encoding="utf-8")


def load_manifest(output_dir):
    path = Path(output_dir) / "metadata" / "manifest.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(output_dir, entry):
    root = ensure_dirs(output_dir)
    path = root / "metadata" / "manifest.json"
    manifest = load_manifest(output_dir)
    manifest = [x for x in manifest if x.get("file") != entry.get("file")]
    manifest.append(entry)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def register_dataset(output_dir, name, file_path, df, frequency, description, fields, notes):
    summary = summarize_df(df)
    save_manifest(output_dir, {
        "name": name,
        "file": str(file_path),
        "frequency": frequency,
        "description": description,
        "fields": fields,
        "rows": summary["rows"],
        "start_date": summary["start_date"],
        "end_date": summary["end_date"],
        "missing_ratio": summary["missing_ratio"],
        "notes": notes,
    })


def get_active_cs_universe(rqdatac, end_date):
    inst = rqdatac.all_instruments(type="CS")
    inst = inst.copy()
    inst["listed_date_dt"] = pd.to_datetime(inst["listed_date"], errors="coerce")
    end = pd.to_datetime(end_date)
    inst = inst[inst["listed_date_dt"].notna() & (inst["listed_date_dt"] <= end)]
    return inst["order_book_id"].dropna().drop_duplicates().tolist()


def chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def date_range_from_csv(path):
    path = Path(path)
    if not path.exists():
        return "", "", 0
    usecols = ["date"]
    try:
        dates = pd.read_csv(path, compression="gzip", usecols=usecols)
    except Exception:
        return "", "", 0
    if len(dates) == 0:
        return "", "", 0
    d = pd.to_datetime(dates["date"], errors="coerce")
    return str(d.min().date()), str(d.max().date()), int(len(dates))
