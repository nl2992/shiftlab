"""Reproduce the bounded, metadata-only Elexon BMRS source audit.

The API response includes quantities, but this script deliberately reports only schema,
publication-time, valid-time, document, revision, row-count, and response-hash metadata.
It does not persist or print any load values and performs no model evaluation.
"""

from __future__ import annotations

import hashlib
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets/{dataset}/stream"
DATASETS = ("ATL", "DATL")
WINDOWS = (
    ("annual_spot", "2023-01-01", "2023-01-02"),
    ("annual_spot", "2024-01-01", "2024-01-02"),
    ("annual_spot", "2025-01-01", "2025-01-02"),
    ("annual_spot", "2026-01-01", "2026-01-02"),
    ("january_2025", "2025-01-01", "2025-02-01"),
    ("dst", "2024-03-31", "2024-04-01"),
    ("dst", "2024-04-01", "2024-04-02"),
    ("dst", "2024-10-27", "2024-10-28"),
    ("dst", "2024-10-28", "2024-10-29"),
    ("coverage", "2022-06-01", "2022-06-02"),
    ("coverage", "2023-06-01", "2023-06-02"),
    ("coverage", "2023-11-01", "2023-11-02"),
    ("coverage", "2024-06-01", "2024-06-02"),
)


def utc_window(start: str, end: str) -> tuple[str, str]:
    """Return the API's explicit UTC timestamps for ISO date bounds."""
    return f"{start}T00:00:00Z", f"{end}T00:00:00Z"


def fetch(dataset: str, start: str, end: str) -> tuple[bytes, list[dict[str, object]]]:
    """Fetch one fixed publication-time window from the unauthenticated BMRS stream."""
    start_utc, end_utc = utc_window(start, end)
    query = urlencode({"publishDateTimeFrom": start_utc, "publishDateTimeTo": end_utc})
    request = Request(
        f"{BASE_URL.format(dataset=dataset)}?{query}",
        headers={"User-Agent": "shiftlab-elexon-metadata-audit/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        body = response.read()
    rows = json.loads(body)
    if not isinstance(rows, list):
        raise TypeError(f"Expected a JSON list for {dataset} {start}–{end}")
    return body, rows


def summarize(
    category: str,
    dataset: str,
    start: str,
    end: str,
    body: bytes,
    rows: list[dict[str, object]],
) -> dict[str, object]:
    """Summarize records without exposing their quantity field."""
    valid_times = sorted({str(row.get("startTime")) for row in rows})
    publish_times = sorted(str(row.get("publishTime")) for row in rows)
    documents = sorted({str(row.get("documentId")) for row in rows})
    revisions = sorted({row.get("documentRevisionNumber") for row in rows}, key=str)
    return {
        "category": category,
        "dataset": dataset,
        "publish_time_window_utc": [start, end],
        "rows": len(rows),
        "distinct_valid_times": len(valid_times),
        "documents": len(documents),
        "revision_values": revisions,
        "publish_time_min": publish_times[0] if publish_times else None,
        "publish_time_max": publish_times[-1] if publish_times else None,
        "valid_time_min": valid_times[0] if valid_times else None,
        "valid_time_max": valid_times[-1] if valid_times else None,
        "response_sha256": hashlib.sha256(body).hexdigest(),
    }


def main() -> None:
    results = []
    for category, start, end in WINDOWS:
        for dataset in DATASETS:
            body, rows = fetch(dataset, start, end)
            results.append(summarize(category, dataset, start, end, body, rows))
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
