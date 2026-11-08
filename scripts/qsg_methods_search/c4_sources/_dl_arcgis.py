"""Shared paged ArcGIS FeatureServer downloader (idempotent, streams to CSV, writes a receipt)."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import requests


def fetch_arcgis(layer_url, fields, where, order, raw: Path, file: str, page_size, threads=3):
    out = raw / file
    if out.exists():
        return
    q = layer_url + "/query"
    cnt = requests.get(
        q, params={"where": where, "returnCountOnly": "true", "f": "json"}, timeout=120
    ).json()["count"]
    cache = raw / "pages"
    cache.mkdir(exist_ok=True)

    def page(off):
        f = cache / f"{off:08d}.json"
        if f.exists():
            return f
        params = {
            "where": where,
            "outFields": fields,
            "returnGeometry": "false",
            "orderByFields": order,
            "resultOffset": off,
            "resultRecordCount": page_size,
            "f": "json",
        }
        for attempt in range(8):
            try:
                r = requests.get(q, params=params, timeout=(10, 60))
                r.raise_for_status()
                p = [x["attributes"] for x in r.json()["features"]]
                f.write_text(json.dumps(p))
                return f
            except Exception:
                if attempt == 7:
                    raise

    with ThreadPoolExecutor(threads) as ex:
        files = list(ex.map(page, range(0, cnt, page_size)))
    cols = fields.split(",")
    tmp = out.with_suffix(out.suffix + ".part")
    n = 0
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for f in files:
            rows = json.loads(f.read_text())
            n += len(rows)
            w.writerows(rows)
    tmp.replace(out)
    (raw / f"{file}.receipt.json").write_text(
        json.dumps(
            {
                "url": q,
                "where": where,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": out.stat().st_size,
                "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "rows": n,
                "server_count": cnt,
            },
            indent=1,
        )
    )
    shutil.rmtree(cache, ignore_errors=True)
