"""Phase 4 optional: 30 guided proposals fitted on Phase-3 full-data results (further development selection).

p4guided : fit sampler on Phase-3 results (out-of-subset dJ), take the first 30 unseen proposals
p4gsub   : screen them on the 12-episode x 2-seed subset (phase tag 4G)
p4gfull  : promote the best 5 by screen dJ (dL <= 0.1 pp) to full data (phase tag 4GF)
"""

from __future__ import annotations

import json
import subprocess
import sys

import pandas as pd
import run_phase345 as p

r12 = p.r12
OUTG = p.OUT / "phase4_guided"


def cid(mods):
    return r12.cid_of(mods)


def guided():
    OUTG.mkdir(exist_ok=True, parents=True)
    S = pd.read_csv(p.TABLES / "phase3_summary.csv")
    S = S[S.scope == "out_of_subset"]
    sc = p.screen_rows()
    rows = []
    for _, r in S.iterrows():
        m = sc.get(r.config_id)
        if not m or r.config_id in p.CONTROLS:
            continue
        rows.append({"combo_id": cid([x["id"] for x in m["modules"]]), "delta_j": r.dJ, "delta_loss_pp": r.dL,
                     "se_j": max((r.dJ_hi - r.dJ_lo) / 3.92, 0.02)})  # fmt: skip
    f = OUTG / "phase3_results.csv"
    pd.DataFrame(rows).drop_duplicates("combo_id").to_csv(f, index=False)
    out = OUTG / "proposals_all.jsonl"
    subprocess.run([sys.executable, str(p.HERE / "paper1_combo_sampler.py"), "guided", "--results", str(f), "--out", str(out),
                    "--seed", "20261110"], check=True)  # fmt: skip
    seen = {r["combo_id"] for r in r12.ledger_rows() if "combo_id" in r}
    props = [json.loads(x) for x in out.read_text().splitlines() if x]
    # sampler rank order, unseen, k >= 2, at most 8 per cardinality (documented diversity rule)
    keep, cnt = [], {}
    for x in props:
        k = len(x["modules"])
        if x["combo_id"] in seen or k < 2 or cnt.get(k, 0) >= 8:
            continue
        cnt[k] = cnt.get(k, 0) + 1
        keep.append(x)
    keep = keep[:30]
    (OUTG / "proposals30.jsonl").write_text("\n".join(json.dumps(x) for x in keep) + "\n")
    print("kept", len(keep), "of", len(props))


def gsub(workers):
    best, _ = r12.best_settings()
    rows = [json.loads(x) for x in (OUTG / "proposals30.jsonl").read_text().splitlines() if x]
    specs, meta = r12.supported_or_record(rows, best, "4G", "P4G", lambda r, m: best[m])
    r12.run_batch("p4g_000", specs, meta, workers)


def gfull(workers):
    L = [r for r in r12.ledger_rows() if r.get("phase") == "4G" and r.get("status") == "OK"]
    L = [r for r in L if r["delta_loss_pp"] <= 0.1]
    L.sort(key=lambda r: r["delta_j"])
    top = L[:5]
    specs, meta = [], {}
    for r in top:
        sp = p.spec_from_ledger_row(r, r["config_id"])
        specs.append(sp)
        meta[r["config_id"]] = {
            "kind": "guided_promoted",
            "screen_dJ": r["delta_j"],
            "k": len(r["modules"]),
        }
    p.run_full("p4g_full", specs, "4GF", meta, workers)


def dispatch(cmd, workers):
    {
        "p4guided": lambda: guided(),
        "p4gsub": lambda: gsub(workers),
        "p4gfull": lambda: gfull(workers),
    }[cmd]()
