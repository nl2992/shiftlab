"""CFPB Consumer Complaint Database (official search API, CSV export): closed with explanation.

Endpoint: https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/
(date_received_min/max, format=csv, no_aggs=true), fetched in calendar-month chunks.
Event = date_received. Label rationale (fixed before downloading, from documentation and domain
knowledge): the company's response to the consumer is "Closed with explanation" for the majority
of complaints, with the remainder closed with monetary/non-monetary relief, without relief, or
untimely. y = (company_response_to_consumer == 'Closed with explanation'); rows still "In progress"
(or blank) are dropped, decided before download. A pre-2020 window is used so the share is not
dominated by the post-2021 credit-reporting surge; the base rate is expected in [0.6, 0.85].
Features at submission: product, sub_product, issue, sub_issue, state, tags, submitted_via,
dow/month. Excluded: company (kept out for simplicity), company response, timely response, consumer
disputed, company public response, date_sent_to_company (after receipt), ZIP, narrative, complaint id.
Window: complaints received 2018-07-01 to 2020-01-01 (ends > 6 years before the fetch).
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
WINDOW = ("2018-07-01", "2020-01-01")
META = {
    "name": "cfpb_complaints",
    "url": URL,
    "license": "CC0 1.0 (CFPB Consumer Complaint Database, public domain)",
    "publisher": "Consumer Financial Protection Bureau",
    "task": "binary: consumer complaint closed with explanation (vs other closures)",
    "label": "company_response_to_consumer == 'Closed with explanation'; In progress/blank dropped",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "received dow/month, product, sub-product, issue, sub-issue, state, tags, submitted via",
}
NUM = ["dow", "month"]
CAT = ["product", "sub_product", "issue", "sub_issue", "state", "tags", "submitted_via"]
FILE = "cfpb_2018-07_2019-12.csv"


def _months():
    s = pd.Timestamp(WINDOW[0])
    e = pd.Timestamp(WINDOW[1])
    while s < e:
        n = s + pd.offsets.MonthBegin(1)
        yield s.strftime("%Y-%m-%d"), n.strftime("%Y-%m-%d")
        s = n


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    h = hashlib.sha256()
    n = 0
    urls = []
    tmp = out.with_suffix(".csv.part")
    with open(tmp, "wb") as f:
        first = True
        for a, b in _months():
            params = {
                "date_received_min": a,
                "date_received_max": b,
                "format": "csv",
                "no_aggs": "true",
                "field": "all",
            }
            for attempt in range(5):
                try:
                    r = requests.get(URL, params=params, timeout=600)
                    r.raise_for_status()
                    break
                except requests.RequestException:
                    if attempt == 4:
                        raise
                    time.sleep(5 * (attempt + 1))
            urls.append(r.url)
            body = r.content
            if not first:
                body = body.split(b"\n", 1)[1]  # drop repeated header
            first = False
            f.write(body)
            h.update(body)
            n += len(body)
    tmp.replace(out)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": URL,
                "chunk_urls": urls,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": n,
                "sha256": h.hexdigest(),
            },
            indent=1,
        )
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    d = d.drop_duplicates("Complaint ID")
    resp = d["Company response to consumer"]
    d = d[resp.notna() & (resp != "In progress")].reset_index(drop=True)
    ts = pd.to_datetime(d["Date received"], errors="coerce", utc=True).dt.tz_localize(None)
    keep = (ts >= WINDOW[0]) & (ts < WINDOW[1])
    d = d[keep].reset_index(drop=True)
    ts = ts[keep].reset_index(drop=True)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": (d["Company response to consumer"] == "Closed with explanation").astype(int),
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "product": d["Product"],
            "sub_product": d["Sub-product"],
            "issue": d["Issue"],
            "sub_issue": d["Sub-issue"],
            "state": d["State"],
            "tags": d["Tags"],
            "submitted_via": d["Submitted via"],
        }
    )
    return out.dropna(subset=["ts"]).sort_values("ts", kind="stable").reset_index(drop=True)
