"""UK police street-level crime (data.police.uk, Open Government Licence v3.0): case outcome.

Force-choice rule (fixed before any download): the single force with the largest recorded crime
volume per public documentation (ONS "Crime in England and Wales: police force area data tables"
and the Home Office), i.e. the Metropolitan Police Service ("metropolitan" files). City of London
is a separate force and is not included.

Label (outcome fields only): among non-ASB crimes whose "Last outcome category" is resolved (not
blank, not "Under investigation"), y = 1 if the outcome is "Investigation complete; no suspect
identified", else 0 (charge/summons, caution, community resolution, evidential difficulties,
prosecution not in public interest, unable to prosecute suspect, etc.). Rows with blank/under-
investigation outcome (all anti-social-behaviour records have no outcome) are dropped. Expected
base rate: Home Office crime-outcome statistics (Crime outcomes in England and Wales, annual
releases) report "investigation complete, no suspect identified" as the single largest closed
outcome, roughly 35-45% of all recorded offences, and the remainder spread over other outcomes;
among resolved cases this puts the rate inside [0.2, 0.8]. Chosen from documentation, not data.

Source archive: the cumulative archive 2026-06.zip is read with HTTP range requests so only the
selected monthly *-metropolitan-street.csv members are downloaded (the archive is ~1.7 GB).
Months 2025-01..2025-05 are used so outcomes are >= 13 months mature at the archive date.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

ARCHIVE = "https://policeuk-data.s3.amazonaws.com/archive/2026-06.zip"
MONTHS = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05"]
META = {
    "name": "uk_police",
    "url": "https://data.police.uk/data/archive/2026-06.zip (members *-metropolitan-street.csv)",
    "license": "Open Government Licence v3.0 (data.police.uk)",
    "publisher": "UK police forces via data.police.uk / Home Office; Metropolitan Police Service",
    "task": "binary: closed crime outcome is 'no suspect identified' (vs any other resolved outcome)",
    "label": "Last outcome category == 'Investigation complete; no suspect identified', "
    "among non-blank, non-'Under investigation' outcomes",
    "delay": 100,
    "window": "2025-01 to 2025-05 reporting months (archive snapshot 2026-06)",
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "report month index, crime type, LSOA code, borough (LSOA name prefix): all "
    "known at report time. Event time is month-resolution only: ts = month start plus one second "
    "per row in file order (ordering within month is the file order).",
}
NUM = ["month_idx"]
CAT = ["crime_type", "lsoa", "borough"]


class _Http(io.RawIOBase):
    def __init__(self, url: str):
        self.u = url
        self.n = int(requests.head(url, timeout=60).headers["Content-Length"])
        self.p = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.p

    def seek(self, o, w=0):
        self.p = {0: o, 1: self.p + o, 2: self.n + o}[w]
        return self.p

    def read(self, k=-1):
        if k < 0:
            k = self.n - self.p
        k = min(k, self.n - self.p)
        if k <= 0:
            return b""
        r = requests.get(self.u, headers={"Range": f"bytes={self.p}-{self.p + k - 1}"}, timeout=300)
        r.raise_for_status()
        self.p += len(r.content)
        return r.content


def _file(m: str) -> str:
    return f"{m}-metropolitan-street.csv"


def fetch(raw: Path) -> None:
    raw.mkdir(parents=True, exist_ok=True)
    if all((raw / _file(m)).exists() for m in MONTHS):
        return
    z = zipfile.ZipFile(_Http(ARCHIVE))
    for m in MONTHS:
        out = raw / _file(m)
        if out.exists():
            continue
        data = z.read(f"{m}/{_file(m)}")
        out.write_bytes(data)
        (raw / f"{_file(m)}.receipt.json").write_text(
            json.dumps(
                {
                    "url": ARCHIVE + f"#{m}/{_file(m)}",
                    "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                },
                indent=1,
            )
        )


def load(raw: Path) -> pd.DataFrame:
    parts = []
    cols = ["Month", "LSOA code", "LSOA name", "Crime type", "Last outcome category"]
    for i, m in enumerate(MONTHS):
        d = pd.read_csv(raw / _file(m), usecols=cols, dtype=str)
        d = d.reset_index(drop=True)
        ts = pd.Timestamp(m + "-01") + pd.to_timedelta(d.index, unit="s")
        oc = d["Last outcome category"]
        res = oc.notna() & (oc != "Under investigation")
        y = (oc == "Investigation complete; no suspect identified").astype(float)
        parts.append(
            pd.DataFrame(
                {
                    "ts": ts,
                    "y": y,
                    "month_idx": i,
                    "crime_type": d["Crime type"],
                    "lsoa": d["LSOA code"],
                    "borough": d["LSOA name"].str.replace(r"\s+\S+$", "", regex=True),
                }
            )[res]
        )
    return pd.concat(parts, ignore_index=True)
