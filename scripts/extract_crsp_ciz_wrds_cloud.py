"""Stream a bounded CRSP CIZ daily extract from an authorized WRDS Cloud session.

This script is intended to run in the user's WRDS Cloud Python environment. It
does not place credentials in code and never overwrites an existing year. A
year is published only after all chunks and a checksum manifest are complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

TABLE = "crspq.wrds_dsfv2_query"
COLUMNS = [
    "permno",
    "permco",
    "dlycaldt",
    "ticker",
    "securitytype",
    "securitysubtype",
    "sharetype",
    "primaryexch",
    "tradingstatusflg",
    "dlydelflg",
    "dlyret",
    "dlyretx",
    "dlyreti",
    "dlyretmissflg",
    "dlyretdurflg",
    "dlyprc",
    "dlyprcflg",
    "dlyprevprc",
    "dlyprevprcflg",
    "dlyvol",
    "dlycap",
    "dlycapflg",
    "dlynumtrd",
    "vwretd",
    "vwretx",
    "ewretd",
    "ewretx",
    "sprtrn",
]
EXCHANGES = ("A", "B", "I", "N", "Q", "R")


def build_query(year: int) -> str:
    """Build one calendar-year query; the end date is exclusive."""
    columns = ",\n                ".join(COLUMNS)
    exchanges = ", ".join(f"'{code}'" for code in EXCHANGES)
    return f"""
        SELECT DISTINCT {columns}
        FROM {TABLE}
        WHERE dlycaldt >= DATE '{year}-01-01'
          AND dlycaldt < DATE '{year + 1}-01-01'
          AND securitytype = 'EQTY'
          AND securitysubtype = 'COM'
          AND sharetype = 'NS'
          AND primaryexch IN ({exchanges})
        ORDER BY permno, dlycaldt
    """.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def query_hash(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def verify_completed_year(year_dir: Path, expected_query_hash: str) -> bool:
    """Return True only if a prior year's manifest and every file checksum match."""
    manifest_path = year_dir / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("query_sha256") != expected_query_hash:
            return False
        files = manifest.get("files")
        if not files or manifest.get("row_count", 0) <= 0:
            return False
        return all(
            (year_dir / entry["name"]).is_file()
            and sha256_file(year_dir / entry["name"]) == entry["sha256"]
            for entry in files
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def extract_year(db: Any, root: Path, year: int, chunk_rows: int) -> int:
    import pandas as pd

    query = build_query(year)
    digest = query_hash(query)
    year_dir = root / f"year={year}"
    if year_dir.exists():
        if verify_completed_year(year_dir, digest):
            print(f"{year}: already complete; checksums verified")
            return 0
        raise FileExistsError(
            f"Refusing to overwrite unverified output at {year_dir}. "
            "Inspect it and choose a new --output directory if needed."
        )

    stage_dir = root / f".year={year}.partial"
    if stage_dir.exists():
        raise FileExistsError(
            f"Incomplete staging output exists at {stage_dir}. "
            "Inspect it before removing it or choose a new --output directory."
        )
    stage_dir.mkdir()

    files: list[dict[str, Any]] = []
    row_count = 0
    previous_key: tuple[int, str] | None = None
    try:
        chunks = db.raw_sql(
            query,
            date_cols=["dlycaldt"],
            coerce_float=False,
            chunksize=chunk_rows,
            return_iter=True,
        )
        for part_number, frame in enumerate(chunks):
            if list(frame.columns) != COLUMNS:
                raise ValueError(f"Unexpected WRDS columns for {year}: {list(frame.columns)!r}")
            if frame.empty:
                continue

            dates = pd.to_datetime(frame["dlycaldt"], errors="coerce")
            if dates.isna().any() or (dates.dt.year != year).any():
                raise ValueError(f"Invalid or out-of-year dlycaldt values in {year} chunk")
            if frame["permno"].isna().any():
                raise ValueError(f"Null permno in {year} chunk")
            if not (
                frame["securitytype"].eq("EQTY").all()
                and frame["securitysubtype"].eq("COM").all()
                and frame["sharetype"].eq("NS").all()
                and frame["primaryexch"].isin(EXCHANGES).all()
            ):
                raise ValueError(f"Universe filter mismatch in {year} chunk")

            keys = list(zip(frame["permno"].astype(int), dates.dt.strftime("%Y-%m-%d")))
            if any(left >= right for left, right in pairwise(keys)):
                raise ValueError(f"Duplicate or unsorted PERMNO/date keys in {year} chunk")
            if previous_key is not None and keys[0] <= previous_key:
                raise ValueError(f"Duplicate or unsorted PERMNO/date boundary in {year}")
            previous_key = keys[-1]

            filename = f"part-{part_number:04d}.csv.gz"
            output_path = stage_dir / filename
            frame.to_csv(output_path, index=False, compression="gzip")
            files.append(
                {
                    "name": filename,
                    "rows": len(frame),
                    "bytes": output_path.stat().st_size,
                    "sha256": sha256_file(output_path),
                }
            )
            row_count += len(frame)
            print(f"{year}: wrote {row_count:,} rows", flush=True)

        if row_count == 0:
            raise ValueError(f"WRDS returned no rows for {year}; year not published")

        manifest = {
            "dataset": "CRSP Stock Version 2/CIZ daily",
            "table": TABLE,
            "year": year,
            "row_count": row_count,
            "query": query,
            "query_sha256": digest,
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "filters": {
                "securitytype": "EQTY",
                "securitysubtype": "COM",
                "sharetype": "NS",
                "primaryexch": list(EXCHANGES),
                "tradingstatusflg": "unfiltered; retain historical inactive/delisted rows",
                "return_flags": "retained without filtering",
            },
            "files": files,
        }
        temporary_manifest = stage_dir / "manifest.json.tmp"
        temporary_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        temporary_manifest.replace(stage_dir / "manifest.json")
        stage_dir.rename(year_dir)
        print(f"{year}: complete ({row_count:,} rows)", flush=True)
        return row_count
    except Exception:
        print(f"{year}: failed; partial files retained at {stage_dir}", flush=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "shiftlab_crsp_ciz_2000_2025_verified",
        help="Private WRDS Cloud output directory (default: a new *_verified directory)",
    )
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--chunk-rows", type=int, default=250_000)
    args = parser.parse_args()

    if args.start_year < 1926 or args.end_year > 2026:
        parser.error("CRSP dictionary coverage is 1925-12-31 through 2026-03-31")
    if args.start_year > args.end_year or args.chunk_rows <= 0:
        parser.error("Invalid year range or chunk size")

    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        import wrds
    except ImportError as exc:
        raise SystemExit(
            "Install/use WRDS's supported Python environment with the `wrds` package."
        ) from exc

    print(f"Writing licensed CRSP files under {output}")
    print("Run this only in WRDS Cloud; no credentials are stored by this script.")
    total_rows = 0
    with wrds.Connection() as db:
        for year in range(args.start_year, args.end_year + 1):
            total_rows += extract_year(db, output, year, args.chunk_rows)
    print(f"Finished requested range; newly extracted rows: {total_rows:,}")


if __name__ == "__main__":
    main()
