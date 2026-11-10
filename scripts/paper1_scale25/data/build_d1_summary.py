"""D1 dev-window summary table (build statistics only; no policy regret, that is WS-B).

One row per dev window: the 26 registered sources (registered C4 window, already opened), the 7 fresh
2025-26 windows (opened, now development), ineligible existing builds (validation statistics only), and the
new dev builds. Validation statistics come from build records. For windows that are development data
(registered/fresh/new) the sealed test-half losses give the mean 0-1 loss of each model and the rate at which
they differ; CONFIRM windows are never built here.

Writes outputs/paper1_scale25/data/d1_summary.csv and docs/paper1_scale25/d1_summary.csv.
"""

import csv
import glob
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper1_scale25/data"
DOCS = ROOT / "docs/paper1_scale25"
inv = json.load(open(OUT / "existing_inventory.json"))
cols = ["dataset_id", "window_kind", "window", "n_events", "episodes", "val_disagreement", "val_err_incumbent", "val_err_challenger",
        "val_err_gap_inc_minus_chal", "val_base_rate", "gates_pass", "gates_failed", "dev_test_err_incumbent", "dev_test_err_challenger",
        "dev_test_diff_rate", "delay", "sealed_hash"]
rows = []


def sealed_stats(path):
    z = np.load(path)
    l0, l1 = z["l0"], z["l1"]
    return float(l0.mean()), float(l1.mean()), float((l0 != l1).mean()), int(z["delay"])


def add(i, kind, win, n, eps, v, gates, sp, h):
    gf = [k for k, ok in gates.items() if not ok]
    e0 = e1 = d = dl = ""
    if sp and Path(sp).exists():
        e0, e1, d, dl = sealed_stats(sp)
    rows.append(dict(dataset_id=i, window_kind=kind, window=win, n_events=n, episodes=eps, val_disagreement=round(v["disagreement"], 5),
                     val_err_incumbent=round(v["err_incumbent"], 5), val_err_challenger=round(v["err_challenger"], 5),
                     val_err_gap_inc_minus_chal=round(v["err_incumbent"] - v["err_challenger"], 5), val_base_rate=round(v["base_rate_y1"], 4),
                     gates_pass=not gf, gates_failed=";".join(gf), dev_test_err_incumbent=e0 if e0 == "" else round(e0, 5),
                     dev_test_err_challenger=e1 if e1 == "" else round(e1, 5), dev_test_diff_rate=d if d == "" else round(d, 5), delay=dl, sealed_hash=h))


for r in inv:
    w = r["meta"]["window"]
    win = f"{w[0][:10]}..{w[1][:10]}" if isinstance(w, list) else str(w)
    kind = "registered-dev" if r.get("registered") else "existing-ineligible-or-excluded"
    add(r["dataset_id"], kind, win, r["n_after_filter"], r["episodes"], r["validation"], r["gates"], r.get("sealed_path") if r.get("registered") else None,
        r.get("registered_hash", ""))
    if "fresh_window" in r:
        fw = r["fresh_window"]
        fv = r["fresh_validation"]
        gates = {"disagreement": fv["disagreement"] >= 0.03, "err_incumbent": 0.02 < fv["err_incumbent"] < 0.5,
                 "err_challenger": 0.02 < fv["err_challenger"] < 0.5, "episodes": r["fresh_episodes"] >= 35}
        add(r["dataset_id"], "fresh-dev(opened 2026-11-09)", f"{fw[0][:10]}..{fw[1][:10]}", "", r["fresh_episodes"], fv, gates,
            r["fresh_sealed_path"] if r.get("fresh_eligible") else None, r.get("fresh_registered_hash") or "")
for p in sorted(glob.glob(str(DOCS / "dev_builds/*.json"))):
    b = json.load(open(p))
    w = b["meta"]["window"]
    sp = ROOT / "data/scale25_dev" / f"{b['name']}.npz"
    add(b["name"], "new-dev", f"{w[0][:10]}..{w[1][:10]}" if isinstance(w, list) else str(w), b["n_after_filter"], b["episodes"], b["validation"], b["gates"],
        sp if b["eligible"] else None, b.get("sealed", {}).get("array_content_sha256", ""))
for d in (OUT, DOCS):
    with open(d / "d1_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
print(len(rows), "rows;", sum(1 for r in rows if r["window_kind"] == "new-dev"), "new")
