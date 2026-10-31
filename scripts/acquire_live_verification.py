"""Archive public forecast/outcome snapshots; no credentials or third-party packages.

Run repeatedly to accumulate prospective evidence. Retrieval time is a conservative
availability bound, never an inferred original publication time. No model evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def utcnow():
    return datetime.now(UTC)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/raw/live_verification"))
    parser.add_argument("--history-days", type=int, default=90)
    args = parser.parse_args()
    if not 0 <= args.history_days <= 365:
        parser.error("--history-days must be between 0 and 365")
    started = utcnow()
    output = args.output / started.strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    records = []

    def fetch(name, url):
        begin = utcnow().isoformat()
        record = {"name": name, "url": url, "request_started_utc": begin}
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": "ShiftLabResearch/1.0 (public data verification)",
                    "Accept": "application/json",
                },
            )
            with urlopen(request, timeout=45) as response:
                raw = response.read(20_000_001)
                record.update(status=response.status, response_headers=dict(response.headers))
            if len(raw) > 20_000_000:
                raise ValueError("Response exceeds 20 MB per-request cap")
            payload = json.loads(raw)
            if isinstance(payload, dict) and (payload.get("error") or payload.get("errors")):
                raise ValueError(str(payload)[:500])
            path = output / (name + ".json")
            path.write_bytes(raw)
            record.update(file=path.name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            if isinstance(payload, dict):
                record["rows"] = len(
                    payload.get(
                        "features", payload.get("data", payload.get("hourly", {}).get("time", []))
                    )
                )
            record["ok"] = True
        except (OSError, ValueError, TypeError, KeyError) as exc:
            payload = None
            record.update(ok=False, error=f"{type(exc).__name__}: {exc}")
        record["retrieved_at_utc"] = utcnow().isoformat()
        records.append(record)
        return payload

    carbon_start = started.strftime("%Y-%m-%dT%H:%MZ")
    jobs = [
        ("carbon_forward", f"https://api.carbonintensity.org.uk/intensity/{carbon_start}/fw48h")
    ]
    # Three climates; station coordinates avoid pretending a city centroid is a station.
    sites = [
        ("jfk", "KJFK", 40.6398, -73.7789),
        ("chicago", "KORD", 41.9786, -87.9048),
        ("phoenix", "KPHX", 33.4342, -112.0116),
    ]
    for name, station, lat, lon in sites:
        query = urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,precipitation,wind_speed_10m",
                "models": "gfs_seamless,ecmwf_ifs025",
                "forecast_days": 7,
                "timezone": "UTC",
            }
        )
        jobs.append((f"open_meteo_{name}", "https://api.open-meteo.com/v1/forecast?" + query))
        jobs.append(
            (
                f"nws_observations_{station}",
                f"https://api.weather.gov/stations/{station}/observations?limit=500",
            )
        )
    end = started.replace(hour=0, minute=0, second=0, microsecond=0)
    cursor = end - timedelta(days=args.history_days)
    while cursor < end:
        stop = min(cursor + timedelta(days=14), end)

        def fmt(t):
            return t.strftime("%Y-%m-%dT%H:%MZ")

        jobs.append(
            (
                f"carbon_history_{cursor:%Y%m%d}",
                f"https://api.carbonintensity.org.uk/intensity/{fmt(cursor)}/{fmt(stop)}",
            )
        )
        cursor = stop
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda job: fetch(*job), jobs))
    for name, station, lat, lon in sites:
        point = fetch(f"nws_point_{name}", f"https://api.weather.gov/points/{lat},{lon}")
        if point:
            url = point.get("properties", {}).get("forecastHourly")
            if url:
                fetch(f"nws_forecast_{name}", url)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    manifest = {
        "purpose": "Acquisition feasibility and prospective snapshot archive; not confirmatory evidence",
        "started_at_utc": started.isoformat(),
        "completed_at_utc": utcnow().isoformat(),
        "code_revision": revision,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "availability_rule": "Use retrieved_at_utc as conservative availability; event/valid time is not release time. Historical data is retrospective only.",
        "sources": sorted(records, key=lambda r: r["name"]),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = {
        "output": str(output.resolve()),
        "successful": sum(r["ok"] for r in records),
        "failed": [r for r in records if not r["ok"]],
        "bytes": sum(r.get("bytes", 0) for r in records),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
