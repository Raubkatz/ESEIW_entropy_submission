#!/usr/bin/env python3
"""
00_merge_projects_to_csv_2026.py

Merge all per-project CSVs from ./nu_files_2026 into one merged dataset in ./merged_csv.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Tuple, Dict

import pandas as pd


# ==============================
# PARAMETERS (SET HERE)
# ==============================

INPUT_DIR = "DATA_ESEIW_final" #important, set correct project directory
OUT_DIR = "DATA_ESEIW_merged_csv"
OUTPUT_NAME = "merged_dataset_2026.csv"
PATTERN = "*.csv"

SCHEMA_CHECK = True
KEEP_EXTRA_COLS = False
WRITE_PARQUET = False

EXPECTED_COLUMNS: List[str] = [ #Input von Philip
    "isSZZBugIntroducer",
    "age",  # ok
    "revision",  # ok
    "nrOfFunctions",  # ok
    "dok0.004Sum",
    "dok0.004AuthorPreCommit",
    "totalLoc",  # ok
    "relativeModified",  # ok
    "dok0.004AuthorPostCommit",
    "modified",  # ok
    "totalAuthors",  # ok
    "dok0.004Avg",
    "totalRefactors",  # ok
    "authors",  # ok
    "isRefactor",  # ok
    "180fileHcpf",  # ok
    "180commitHcpf",  # ok
]


def sniff_delimiter(path: Path, sample_bytes: int = 64_000) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            sample = f.read(sample_bytes)
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except Exception:
        return ","


def project_name_from_file(path: Path) -> str:
    return path.stem


def read_csv_flex(path: Path) -> pd.DataFrame:
    delim = sniff_delimiter(path)
    try:
        return pd.read_csv(path, sep=delim, low_memory=False, encoding="utf-8")
    except Exception:
        return pd.read_csv(path, sep=delim, low_memory=False, encoding="utf-8", engine="python")


def align_schema(
    df: pd.DataFrame,
    expected_cols: List[str],
    file_tag: str,
    strict: bool = True
) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:

    current = list(df.columns)
    missing = [c for c in expected_cols if c not in df.columns]
    extra = [c for c in df.columns if c not in expected_cols]

    for c in missing:
        df[c] = pd.NA

    if strict:
        df = df[expected_cols]

    report = {
        "file": [file_tag],
        "missing_cols": missing,
        "extra_cols": extra,
        "original_col_count": [len(current)],
        "final_col_count": [len(df.columns)],
    }
    return df, report


def main() -> None:

    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob(PATTERN))
    if not files:
        raise SystemExit(f"No files matched {PATTERN} in {in_dir.resolve()}")

    merged_chunks: List[pd.DataFrame] = []
    file_reports: List[dict] = []

    for p in files:
        df = read_csv_flex(p)

        df["source_file"] = p.name
        df["source_project"] = project_name_from_file(p)

        print(project_name_from_file(p))

        if SCHEMA_CHECK:
            df, rep = align_schema(
                df,
                EXPECTED_COLUMNS,
                file_tag=p.name,
                strict=True,
            )
            rep["rows"] = [int(len(df))]
            file_reports.append(rep)
        else:
            df, rep = align_schema(
                df,
                EXPECTED_COLUMNS,
                file_tag=p.name,
                strict=True,
            )
            rep["rows"] = [int(len(df))]
            file_reports.append(rep)

        merged_chunks.append(df)

    merged = pd.concat(merged_chunks, ignore_index=True)
    merged = merged[EXPECTED_COLUMNS]

    out_csv = out_dir / OUTPUT_NAME
    merged.to_csv(out_csv, index=False)

    report_path = out_dir / "merge_report.json"

    normalized = []
    for r in file_reports:
        normalized.append({
            "file": r["file"][0],
            "rows": r["rows"][0],
            "missing_cols": r["missing_cols"],
            "extra_cols": r["extra_cols"],
            "original_col_count": r["original_col_count"][0],
            "final_col_count": r["final_col_count"][0],
        })

    summary = {
        "input_dir": str(in_dir.resolve()),
        "out_csv": str(out_csv.resolve()),
        "file_count": len(files),
        "total_rows": int(len(merged)),
        "schema_check": SCHEMA_CHECK,
        "kept_extra_cols": KEEP_EXTRA_COLS,
        "per_file": normalized,
        "final_columns": list(merged.columns),
    }

    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if WRITE_PARQUET:
        try:
            out_parquet = out_dir / (Path(OUTPUT_NAME).stem + ".parquet")
            merged.to_parquet(out_parquet, index=False)
        except Exception as e:
            print(f"[WARN] Could not write parquet: {e}")

    print(f"[OK] Merged {len(files)} files -> {out_csv} ({len(merged)} rows)")
    print(f"[OK] Report -> {report_path}")


if __name__ == "__main__":
    main()