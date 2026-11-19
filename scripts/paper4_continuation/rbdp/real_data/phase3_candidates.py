"""Phase 3 (Addendum B) step 1: build the candidate item list from the Rdatasets index. No series is fetched here
other than HEAD requests for CSV size. Writes results/phase3_candidates.json.

Judgements (declared): regex is applied to the index `Title` column (the index has no separate documentation title);
the `datasets`-package time-series objects are the fixed list DATASETS_TS below (names of ts objects from the R
documentation); items used in Phases 1-2 are excluded; order = plain Python sort on (Package, Item).
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data/raw/real_chains/phase3"
OUT = ROOT / "docs/paper4_continuation/rbdp/real_data/results/phase3_candidates.json"
REGEX = r"(?i)(time series|monthly|quarterly|annual|yearly|daily|weekly|hourly|per year|per month)"
DATASETS_TS = ["AirPassengers", "BJsales", "BJsales.lead", "EuStockMarkets", "JohnsonJohnson", "LakeHuron", "Nile",
               "Seatbelts", "UKDriverDeaths", "UKgas", "USAccDeaths", "WWWusage", "airmiles", "austres", "co2",
               "discoveries", "fdeaths", "ldeaths", "lh", "lynx", "mdeaths", "nhtemp", "nottem", "presidents",
               "sunspot.month", "sunspot.year", "sunspots", "treering", "uspop"]
USED = {("datasets", i) for i in ["lynx", "sunspot.year", "nottem", "airquality", "Nile", "LakeHuron", "discoveries",
                                  "nhtemp", "EuStockMarkets", "AirPassengers", "UKgas", "USAccDeaths", "presidents",
                                  "co2", "faithful"]} | {("MASS", "geyser")}
MAX_BYTES = 1_000_000


def main() -> None:
    rows = list(csv.DictReader(open(RAW / "datasets.csv", encoding="utf-8")))
    cand, rejected = [], []
    for r in rows:
        key = (r["Package"], r["Item"])
        why = []
        if re.search(REGEX, r["Title"]):
            why.append("title matches regex")
        if r["Package"] == "datasets" and r["Item"] in DATASETS_TS:
            why.append("datasets-package ts object (fixed list)")
        if not why:
            continue
        nrow = int(r["Rows"])
        if not 80 <= nrow <= 5000:
            rejected.append(dict(key=key, reason=f"rows={nrow} outside 80..5000"))
            continue
        if key in USED:
            rejected.append(dict(key=key, reason="already used / shared-source exclusion"))
            continue
        cand.append(dict(package=r["Package"], item=r["Item"], title=r["Title"], rows=nrow, csv=r["CSV"], reasons=why))
    cand.sort(key=lambda c: (c["package"], c["item"]))
    final = []
    for c in cand:
        try:
            h = requests.head(c["csv"], timeout=60, allow_redirects=True, headers={"User-Agent": "research-fetch/1.0"})
            cl = int(h.headers.get("Content-Length", -1))
            c["content_length"] = cl
            if h.status_code != 200 or cl < 0:
                rejected.append(dict(key=(c["package"], c["item"]), reason=f"HEAD status {h.status_code}, length {cl}"))
            elif cl > MAX_BYTES:
                rejected.append(dict(key=(c["package"], c["item"]), reason=f"size {cl} > 1 MB"))
            else:
                final.append(c)
        except requests.RequestException as ex:
            rejected.append(dict(key=(c["package"], c["item"]), reason=f"HEAD failed {ex}"))
    OUT.write_text(json.dumps(dict(
        regex=REGEX, regex_applied_to="index Title column", datasets_ts_fixed_list=DATASETS_TS,
        excluded_used=sorted(map(list, USED)), order="sorted by (Package, Item), plain string order",
        index_rows=len(rows), n_after_title_rows_unused=len(cand), n_final=len(final), candidates=final,
        rejected=rejected), indent=1, default=str))
    print(len(rows), len(cand), len(final), len(rejected))


if __name__ == "__main__":
    main()
