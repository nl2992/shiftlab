"""Acquire bounded WRDS finance panels for the ShiftLab CRSP study.

Run in an authenticated WRDS Cloud/Jupyter Python environment. The script stores
licensed extracts locally in that environment, streams compressed CSV parts, and
refuses to overwrite an existing partition. It never embeds or writes credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

START_YEAR = 2000
END_YEAR = 2025
TABLES = {
    "factors": ("ff.factors_daily", ("date",)),
    "treasury": ("crsp_a_treasuries.tfz_dly_rf2", ("caldt", "date", "tdcaldt")),
    "compustat": ("compd.funda", ("datadate",)),
}
FACTOR_COLUMNS = ("date", "mktrf", "smb", "hml", "rmw", "cma", "rf", "umd")
COMPUSTAT_COLUMNS = (
    "gvkey",
    "datadate",
    "fyear",
    "fyr",
    "rdq",
    "tic",
    "cusip",
    "conm",
    "indfmt",
    "consol",
    "popsrc",
    "datafmt",
    "sic",
    "naics",
    "at",
    "sale",
    "revt",
    "ni",
    "ib",
    "ceq",
    "dltt",
    "dlc",
    "act",
    "lct",
    "che",
    "csho",
    "cshoq",
    "prcc_f",
    "epspx",
    "xrd",
    "capx",
)
COMPUSTAT_FILTERS = {"indfmt": "INDL", "consol": "C", "popsrc": "D", "datafmt": "STD"}
TAQ_TABLES = {"trades": "taqmsec.ctm", "quotes": "taqmsec.cqm"}
IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def quote_table(table: str) -> str:
    schema, name = table.split(".", 1)
    if not IDENTIFIER.fullmatch(schema) or not IDENTIFIER.fullmatch(name):
        raise ValueError(f"Unsafe table name: {table!r}")
    return f'"{schema}"."{name}"'


def columns_for(db: Any, table: str) -> list[str]:
    schema, name = table.split(".", 1)
    if not IDENTIFIER.fullmatch(schema) or not IDENTIFIER.fullmatch(name):
        raise ValueError(f"Unsafe table name: {table!r}")
    rows = db.raw_sql(
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = '{schema}' AND table_name = '{name}' "
        "ORDER BY ordinal_position"
    )
    return rows["column_name"].astype(str).tolist()


def resolve_date_column(columns: list[str], candidates: tuple[str, ...]) -> str:
    lower = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    raise ValueError(f"No known date field {candidates!r}; available fields: {columns!r}")


def choose_table(db: Any, candidates: tuple[str, ...]) -> tuple[str, list[str]]:
    failures = []
    for table in candidates:
        columns = columns_for(db, table)
        if columns:
            return table, columns
        failures.append(f"{table}: missing or not subscribed")
    raise RuntimeError("Could not find an accessible table: " + "; ".join(failures))


def publish_partition(
    db: Any,
    *,
    table: str,
    columns: list[str],
    date_column: str,
    start: date,
    end: date,
    out_dir: Path,
    chunk_rows: int,
    source: str,
    filters: dict[str, str] | None = None,
    extra_where: str = "",
    order_columns: tuple[str, ...] = (),
) -> int:
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {out_dir}")
    out_dir.mkdir(parents=True)
    selected = ", ".join(f'"{col}"' for col in columns)
    clauses = [
        f"\"{date_column}\" >= DATE '{start.isoformat()}'",
        f"\"{date_column}\" < DATE '{end.isoformat()}'",
    ]
    for col, value in (filters or {}).items():
        clauses.append(f"\"{col}\" = '{value}'")
    if extra_where:
        clauses.append(extra_where)
    order = tuple(dict.fromkeys((date_column, *order_columns)))
    order_by = ", ".join(f'"{col}"' for col in order)
    query = (
        f"SELECT {selected} FROM {quote_table(table)} WHERE "
        + " AND ".join(clauses)
        + f" ORDER BY {order_by}"
    )
    query_sha = hashlib.sha256(query.encode("utf-8")).hexdigest()
    parts: list[dict[str, Any]] = []
    row_count = 0
    try:
        chunks = db.raw_sql(query, chunksize=chunk_rows, return_iter=True, coerce_float=False)
        for part_number, frame in enumerate(chunks):
            if list(frame.columns) != columns:
                raise ValueError(f"Unexpected columns from {table}: {list(frame.columns)!r}")
            if frame.empty:
                continue
            filename = f"part-{part_number:05d}.csv.gz"
            output = out_dir / filename
            frame.to_csv(output, index=False, compression="gzip")
            parts.append(
                {
                    "name": filename,
                    "rows": len(frame),
                    "bytes": output.stat().st_size,
                    "sha256": digest_file(output),
                }
            )
            row_count += len(frame)
            print(f"{source} {start.year}: {row_count:,} rows", flush=True)
        if not row_count:
            raise ValueError(f"No rows returned for {source} [{start}, {end})")
        manifest = {
            "source": source,
            "table": table,
            "date_column": date_column,
            "start_inclusive": start.isoformat(),
            "end_exclusive": end.isoformat(),
            "row_count": int(row_count),
            "columns": columns,
            "filters": filters or {},
            "query_sha256": query_sha,
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "files": parts,
        }
        temp = out_dir / "manifest.json.tmp"
        temp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        temp.replace(out_dir / "manifest.json")
        print(f"{source} {start.year}: complete ({row_count:,} rows)", flush=True)
        return int(row_count)
    except Exception:
        print(f"{source}: failed; partial output retained at {out_dir}", flush=True)
        raise


def extract_annual_source(
    db: Any, root: Path, name: str, chunk_rows: int, start_year: int, end_year: int
) -> None:
    table_candidates = {
        "factors": ("ff.factors_daily",),
        "treasury": ("crsp_a_treasuries.tfz_dly_rf2", "crsp_a_treasuries.tfz_dly"),
        "compustat": ("compd.funda", "comp_na_daily_all.funda"),
    }
    table, available = choose_table(db, table_candidates[name])
    date_col = resolve_date_column(available, TABLES[name][1])
    if name == "factors":
        columns = [col for col in FACTOR_COLUMNS if col in available]
        if not {"date", "mktrf", "rf"}.issubset(columns):
            raise ValueError(f"Expected daily factor fields not found in {table}: {available!r}")
        filters: dict[str, str] = {}
        order = ()
    elif name == "treasury":
        # Preserve the small daily risk-free-rate table's native fields for auditability.
        columns = available
        filters = {}
        order = ()
    else:
        columns = [col for col in COMPUSTAT_COLUMNS if col in available]
        if not {"gvkey", "datadate"}.issubset(columns):
            raise ValueError(f"Compustat key fields missing from {table}: {available!r}")
        filters = {key: value for key, value in COMPUSTAT_FILTERS.items() if key in columns}
        order = ("gvkey",)
    print(f"{name}: {table}; date={date_col}; fields={len(columns)}")
    for year in range(start_year, end_year + 1):
        publish_partition(
            db,
            table=table,
            columns=columns,
            date_column=date_col,
            start=date(year, 1, 1),
            end=date(year + 1, 1, 1),
            out_dir=root / name / f"year={year}",
            chunk_rows=chunk_rows,
            source=name,
            filters=filters,
            order_columns=order,
        )


def extract_ccm_links(db: Any, root: Path, chunk_rows: int) -> None:
    """Export CCM link-history records overlapping the study window."""
    table, available = choose_table(db, ("crsp.ccmxpf_lnkhist", "crsp.ccmxpf_linktable"))
    required = {"gvkey", "lpermno", "linkdt", "linkenddt"}
    if not required.issubset(available):
        raise ValueError(f"CCM link keys missing from {table}: {available!r}")
    columns = [
        col
        for col in ("gvkey", "lpermno", "linkdt", "linkenddt", "linktype", "linkprim")
        if col in available
    ]
    # A broad lower bound preserves old links that remain active into the study period.
    overlap = (
        "\"linkdt\" < DATE '2026-01-01' AND "
        '("linkenddt" IS NULL OR "linkenddt" >= DATE \'2000-01-01\')'
    )
    publish_partition(
        db,
        table=table,
        columns=columns,
        date_column="linkdt",
        start=date(1900, 1, 1),
        end=date(2026, 1, 1),
        out_dir=root / "ccm_links" / "study_window",
        chunk_rows=chunk_rows,
        source="ccm_crsp_compustat_link_history",
        extra_where=overlap,
        order_columns=("gvkey", "lpermno"),
    )


def read_symbols(path: Path) -> list[str]:
    symbols = sorted(
        {
            line.strip().upper()
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
    )
    if not symbols:
        raise ValueError("Symbol file contains no symbols")
    if any(not re.fullmatch(r"[A-Z0-9.\-]+", symbol) for symbol in symbols):
        raise ValueError("Symbols must contain only letters, digits, dot, or hyphen")
    return symbols


def extract_taq(
    db: Any, root: Path, start: date, end: date, symbols_file: Path, kind: str, chunk_rows: int
) -> None:
    span = (end - start).days + 1
    if span <= 0 or span > 365:
        raise ValueError("TAQ request must cover 1–365 calendar days (end date is inclusive)")
    symbols = read_symbols(symbols_file)
    quoted_symbols = ", ".join("'" + symbol.replace("'", "''") + "'" for symbol in symbols)
    for product in ("trades", "quotes") if kind == "both" else (kind,):
        table, available = choose_table(db, (TAQ_TABLES[product],))
        date_col = resolve_date_column(available, ("date", "tradedate"))
        symbol_col = next((col for col in available if col.lower() == "sym_root"), None)
        if symbol_col is None:
            raise ValueError(f"TAQ symbol field sym_root not found in {table}")
        # These are typical TAQ fields; preserve whichever are present in the subscribed vintage.
        preferred = (
            ("date", "time_m", "sym_root", "sym_suffix", "price", "size", "ex", "cond", "tr_scond")
            if product == "trades"
            else (
                "date",
                "time_m",
                "sym_root",
                "sym_suffix",
                "bid",
                "ofr",
                "bidsiz",
                "ofrsiz",
                "ex",
                "mode",
                "qu_cond",
            )
        )
        columns = [col for col in preferred if col in available]
        if date_col not in columns:
            columns.insert(0, date_col)
        if symbol_col not in columns:
            columns.append(symbol_col)
        symbol_sql = f'"{symbol_col}" IN ({quoted_symbols})'
        end_exclusive = end + timedelta(days=1)
        out = root / "taq" / product / f"{start.isoformat()}_to_{end.isoformat()}"
        publish_partition(
            db,
            table=table,
            columns=columns,
            date_column=date_col,
            start=start,
            end=end_exclusive,
            out_dir=out,
            chunk_rows=chunk_rows,
            source=f"taq_{product}",
            extra_where=symbol_sql,
            order_columns=("time_m", symbol_col) if "time_m" in columns else (symbol_col,),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path.home() / "shiftlab_wrds_finance_2000_2025"
    )
    parser.add_argument("--start-year", type=int, default=START_YEAR)
    parser.add_argument("--end-year", type=int, default=END_YEAR)
    parser.add_argument("--chunk-rows", type=int, default=200_000)
    parser.add_argument(
        "--skip", choices=("factors", "treasury", "compustat"), action="append", default=[]
    )
    parser.add_argument("--skip-ccm-links", action="store_true")
    parser.add_argument("--taq-kind", choices=("trades", "quotes", "both"))
    parser.add_argument("--taq-start", type=date.fromisoformat)
    parser.add_argument(
        "--taq-end", type=date.fromisoformat, help="Inclusive end date; max 365-day span"
    )
    parser.add_argument("--taq-symbols-file", type=Path)
    args = parser.parse_args()
    if args.chunk_rows < 1:
        parser.error("--chunk-rows must be positive")
    if args.start_year < 1926 or args.end_year > 2026 or args.start_year > args.end_year:
        parser.error("Invalid year range (supported study years: 2000–2025; choose a valid range)")
    if args.taq_kind and not (args.taq_start and args.taq_end and args.taq_symbols_file):
        parser.error("TAQ requires --taq-kind, --taq-start, --taq-end, and --taq-symbols-file")
    if not args.taq_kind and any((args.taq_start, args.taq_end, args.taq_symbols_file)):
        parser.error("Specify all TAQ options together, including --taq-kind")

    try:
        import wrds
    except ImportError as exc:
        raise SystemExit(
            "Run in WRDS Cloud's Python environment, which provides the wrds package"
        ) from exc
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    print(f"Writing licensed WRDS extracts under {output}")
    print("No credentials are stored. TAQ is opt-in and requires a narrow symbol/date slice.")
    with wrds.Connection() as db:
        for name in ("factors", "treasury", "compustat"):
            if name not in args.skip:
                extract_annual_source(
                    db, output, name, args.chunk_rows, args.start_year, args.end_year
                )
        if not args.skip_ccm_links:
            extract_ccm_links(db, output, args.chunk_rows)
        if args.taq_kind:
            extract_taq(
                db,
                output,
                args.taq_start,
                args.taq_end,
                args.taq_symbols_file,
                args.taq_kind,
                args.chunk_rows,
            )
    print("WRDS acquisition completed. Validate manifests and checksums before transfer.")


if __name__ == "__main__":
    main()
