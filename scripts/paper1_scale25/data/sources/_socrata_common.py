"""Shared factory for Socrata-hosted scale-25 recipes (same interface as c4_sources modules).

A recipe file defines CFG and calls ``globals().update(make_module(CFG))``. The factory builds META,
NUM, CAT, WINDOW, fetch() and load(). The label is always
    y = 1 if (close_ts - open_ts) <= thresh_days   (still-open or missing close = 0)
or, when ``label_fn`` is given, y = label_fn(raw_dataframe) (a 0/1 Series, NaN allowed -> row dropped).
Features are recorded at event creation; outcome fields only enter the label.

CFG keys: name, domain, rid, open_col, close_col, thresh_days, window, cat (feature name -> source column),
extra_num (feature name -> source column, numeric), publisher, license, page, task, features_note, delay,
label_text, where_extra (optional SoQL clause), label_cols (extra columns needed for label_fn).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

PAGE = 100_000


def make_module(cfg: dict) -> dict:
    name, dom, rid = cfg["name"], cfg["domain"], cfg["rid"]
    oc, cc = cfg["open_col"], cfg.get("close_col")
    win = cfg["window"]
    cat_map, num_map = cfg["cat"], cfg.get("extra_num", {})
    url = f"https://{dom}/resource/{rid}.csv"
    thresh = cfg.get("thresh_days")
    label_fn = cfg.get("label_fn")
    file = f"{name}_{win[0][:7]}_{win[1][:7]}.csv"
    cols = [oc] + ([cc] if cc else []) + list(cat_map.values()) + list(num_map.values()) + list(cfg.get("label_cols", []))
    cols = list(dict.fromkeys(cols))

    META = {
        "name": name,
        "url": f"https://{dom}/resource/{rid}  ({cfg.get('page', '')})",
        "license": cfg["license"],
        "publisher": cfg["publisher"],
        "task": cfg["task"],
        "label": cfg["label_text"],
        "delay": cfg.get("delay", 100),
        "window": win,
        "subsample_rule": "c4_build.N_MAX systematic",
        "features_note": cfg["features_note"],
    }
    NUM = ["hour", "dow", "month"] + list(num_map)
    CAT = list(cat_map)

    def fetch(raw: Path) -> None:
        out = raw / file
        if out.exists():
            return
        where = f"{oc} >= '{win[0]}' AND {oc} < '{win[1]}'"
        if cfg.get("where_extra"):
            where += f" AND ({cfg['where_extra']})"
        cnt = requests.get(
            f"https://{dom}/resource/{rid}.json",
            params={"$select": "count(*) as n", "$where": where},
            timeout=300,
        ).json()[0]["n"]
        order = f"{oc},:id"
        t = requests.get(url, params={"$select": oc, "$where": where, "$order": order, "$limit": 1}, timeout=300)
        if t.status_code != 200:
            order = oc  # dataset has no usable :id; ties may reorder across pages (recorded in receipt)
        parts = []
        tot_bytes = 0
        hh = hashlib.sha256()
        tmp = out.with_suffix(".csv.part")
        with open(tmp, "wb") as fh:
            first = True
            for off in range(0, int(cnt), PAGE):
                params = {"$select": ",".join(cols), "$where": where, "$order": order, "$limit": PAGE, "$offset": off}
                for attempt in range(6):
                    try:
                        r = requests.get(url, params=params, timeout=(20, 600))
                        r.raise_for_status()
                        break
                    except Exception:
                        if attempt == 5:
                            raise
                body = r.content
                if not first:
                    body = body.split(b"\n", 1)[1] if b"\n" in body else b""
                first = False
                fh.write(body)
                hh.update(body)
                tot_bytes += len(body)
                parts.append(off)
        tmp.rename(out)
        (raw / f"{file}.receipt.json").write_text(
            json.dumps(
                {
                    "url": url,
                    "where": where,
                    "server_count": int(cnt),
                    "order": order,
                    "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                    "bytes": tot_bytes,
                    "sha256": hh.hexdigest(),
                },
                indent=1,
            )
        )

    def load(raw: Path) -> pd.DataFrame:
        d = pd.read_csv(raw / file, dtype=str)
        ts = pd.to_datetime(d[oc], errors="coerce")
        if label_fn is not None:
            y = pd.to_numeric(label_fn(d, ts), errors="coerce")
        else:
            closed = pd.to_datetime(d[cc], errors="coerce")
            y = ((closed - ts) <= pd.Timedelta(days=thresh)).astype(int)  # NaT -> False -> 0
        out = {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
        for f, c in cat_map.items():
            out[f] = d[c]
        for f, c in num_map.items():
            out[f] = pd.to_numeric(d[c], errors="coerce")
        o = pd.DataFrame(out)
        return o.dropna(subset=["ts", "y"])

    return {"META": META, "NUM": NUM, "CAT": CAT, "WINDOW": win, "fetch": fetch, "load": load, "CFG": cfg}
