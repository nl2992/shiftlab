"""Kill-test runner for candidate E. Appends to the dualuse ledger."""

import argparse
import dataclasses
import json
import pathlib
import subprocess
import time

import numpy as np

from shiftlab.paper3.dualuse.sim import KillCfg, forward_gap, run_chunk, wilson

LEDGER = pathlib.Path("papers/paper3_cost_aware_adaptation/2026_programme/ledger/dualuse.jsonl")
# registered ranges: smoke 9_000_000-9_099_999, dev 9_100_000-9_199_999 (seed-off shifts within)
DEV_BASE = 9_100_000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--R", type=int, default=20000)
    ap.add_argument("--chunk", type=int, default=2500)
    ap.add_argument("--base", type=int, default=DEV_BASE)
    ap.add_argument("--cfg", type=json.loads, default={})
    a = ap.parse_args()
    cfg = KillCfg(**a.cfg)
    t0 = time.time()
    bank = np.random.default_rng(a.base + 99999).standard_normal((20000, cfg.d)).astype(np.float32)
    n_all = 0
    cnt = {g: 0 for g in cfg.gates}
    fwd = {h: [] for h in cfg.horizons}
    fwdh = {h: [] for h in cfg.horizons}
    for c in range(a.R // a.chunk):
        out = run_chunk(cfg, a.chunk, np.random.default_rng([a.base, c]))
        for g in cfg.gates:
            cnt[g] += int((out["promo"][g] >= 0).sum())
        gp = forward_gap(cfg, out, bank)
        gh = (
            forward_gap(cfg, out, bank, which="snap_hold", gate="holdout")
            if "holdout" in cfg.gates
            else None
        )
        for h in cfg.horizons:
            fwd[h].append(gp[h])
            if gh is not None:
                fwdh[h].append(gh[h])
        n_all += a.chunk
    res = {"n": n_all, "alpha": cfg.alpha, "rates": {}, "forward": {}}
    for g in cfg.gates:
        lo, hi = wilson(cnt[g], n_all)
        res["rates"][g] = {"k": cnt[g], "rate": cnt[g] / n_all, "ci": [round(lo, 5), round(hi, 5)]}
    for h in cfg.horizons:
        for nm, store in (("", fwd), ("_holdout", fwdh)):
            if not store[h]:
                continue
            v = np.concatenate(store[h])
            pm = ~np.isnan(v)
            k = int((v[pm] <= 1e-3).sum())  # promoted AND forward value <= 0 (no benefit)
            lo, hi = wilson(k, n_all)
            res["forward"][str(h) + nm] = {
                "n_promoted": int(pm.sum()),
                "mean_V_given_promoted": float(v[pm].mean()) if pm.any() else None,
                "frac_V_pos_given_promoted": float((v[pm] > 1e-3).mean()) if pm.any() else None,
                "false_prom_forward_rate": k / n_all,
                "ci": [round(lo, 5), round(hi, 5)],
            }
    try:
        sha = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
            + "+dirty"
        )
    except Exception:  # noqa: BLE001
        sha = "unknown"
    rec = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git_sha": sha,
        "kind": "dualuse_kill",
        "tag": a.tag,
        "config": dataclasses.asdict(cfg),
        "seeds": f"base {a.base}, chunks 0..{a.R // a.chunk - 1}",
        "status": "complete",
        "wall_s": round(time.time() - t0, 1),
        "result": res,
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(a.tag, json.dumps(res["rates"]))
    for h, r in res["forward"].items():
        print("  h", h, r)


if __name__ == "__main__":
    main()
