"""SOTA sprint screening runner: paired synthetic (or cached real) streams x chosen policies.

Synthetic seed ``s`` of regime ``R`` draws one loss stream from
``SeedSequence([seed_base, sha(R_base), s])``; every policy replays that stream with its own
private generator, so all comparisons are paired. A ``@B<n>`` regime suffix changes the hard budget.

    uv run python scripts/sota_sprint/screen.py --regimes F0_better,F0_null \
        --policies QSG,xu_acquisition_only --seeds 20 --out outputs/sota_sprint/screen/demo
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT / "scripts/failure_atlas_v2_flq", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from bench import CONTRACT, DEV_SEED_BASE, parse_regime  # noqa: E402
import validation_spec  # noqa: E402,F401  (registers the W_* validation regimes)
from regimes import expected_oracle_path, hindsight_oracle_cost  # noqa: E402
from suite import build_suite, stream_from_losses  # noqa: E402  (also adds the simulator path)
from simulator import run_episode  # noqa: E402

LOSS_DIR = ROOT / "data/atlas_v2_losses"
REAL_DELAYS = {"rialto": 100, "spam": 50, "weather": 1, "openml_ldpa": 100, "uci_occupancy": 100,
               "airlines": 100, "bank": 100, "elec2": 48, "criteo": 100}


def _h(s: str) -> int:
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4], "big")


def metrics(pol, losses, gain, *, delay, budget, cq, cs, stream_rng) -> dict:
    preds, labels = stream_from_losses(losses, stream_rng)
    t0 = time.perf_counter()
    res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                      label_price=cq, switch_cost=cs, trace=True)
    runtime = time.perf_counter() - t0
    if res.requested_labels > budget:
        raise AssertionError(f"{pol.name} exceeded budget")
    rec = res.records
    dep = np.fromiter((r["deployed_model"] for r in rec), int, len(rec))
    req = np.fromiter((r["requested"] for r in rec), int, len(rec))
    Tn = len(dep)
    req_t = np.flatnonzero(req)
    first1 = int(np.argmax(dep == 1)) if (dep == 1).any() else -1
    better, worse = gain > 0, gain < 0
    on_wrong = ((dep == 1) & worse) | ((dep == 0) & better)
    trans = np.diff(np.r_[0, dep])
    pending = np.convolve(req, np.ones(max(delay, 1), int))[:Tn]  # requested, not yet released
    onset = int(np.argmax(better)) if better.any() else -1
    after = np.flatnonzero((dep == 1) & (np.arange(Tn) >= onset)) if onset >= 0 else []
    exp_path = expected_oracle_path(gain, cs)
    exp_cost = float(np.sum(losses[np.arange(Tn), exp_path])
                     + cs * np.sum(np.diff(np.r_[0, exp_path]) != 0))
    return {
        "net": res.net_cost, "loss": res.prediction_loss, "labels": res.requested_labels,
        "switches": res.deployment_switches, "first_deploy": first1, "final": int(dep[-1]),
        "ever_promote": int(first1 >= 0), "n_promotions": int((trans == 1).sum()),
        "n_rollbacks": int((trans == -1).sum()),
        "frac_on_wrong": float(on_wrong.mean()),
        "detect_delay": int(after[0] - onset) if len(after) else -1,
        "labels_by_500": int((req_t < 500).sum()),
        "labels_after_1000": int((req_t >= 1000).sum()),
        "exhaust_t": int(req_t[budget - 1]) if len(req_t) >= budget else Tn,
        "max_pending": int(pending.max()) if Tn else 0,
        "excess_vs_expected_G": float(np.sum(np.where(dep == 1, -gain, 0.0))),
        "regret_hindsight": res.net_cost - hindsight_oracle_cost(losses, cs),
        "regret_expected_oracle": res.net_cost - exp_cost,
        "runtime_s": round(runtime, 4),
    }


def _job(args):
    kind, name, ep, seed, seed_base, names = args
    from registry import EXTRA

    if kind == "synthetic":
        R, b = parse_regime(name)
        budget = b or CONTRACT["budget"]
        losses = R.sample(np.random.default_rng(np.random.SeedSequence(
            [seed_base, _h(R.name), seed])))
        gain, delay = R.truth_gain(), R.delay
    else:
        z = np.load(LOSS_DIR / f"{name}.npz")
        losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
        gain = np.full(losses.shape[0], float((losses[:, 0].astype(int) - losses[:, 1]).mean()))
        delay, budget = REAL_DELAYS[name], CONTRACT["budget"]
    rows = []
    run_ep = ep * 100_000 + seed
    for pol in build_suite(losses.shape[0], budget, CONTRACT["cs"], CONTRACT["cq"],
                           CONTRACT["alpha"], delay, run_ep, seed_base + _h(name) % 1000,
                           names=names, extra=EXTRA):
        stream_rng = np.random.default_rng([seed_base, _h(name), ep, seed, 7])
        m = metrics(pol, losses, gain, delay=delay, budget=budget, cq=CONTRACT["cq"],
                    cs=CONTRACT["cs"], stream_rng=stream_rng)
        rows.append({"kind": kind, "regime": name, "ep": ep, "seed": seed, "policy": pol.name,
                     "delay": delay, "budget": budget, **m})
    return rows


def _git_rev() -> str:
    try:
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = subprocess.call(["git", "diff", "--quiet", "--", "scripts"], cwd=ROOT) != 0
        return rev + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kind", choices=("synthetic", "real"), default="synthetic")
    ap.add_argument("--regimes", required=True)
    ap.add_argument("--policies", required=True)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--seed-base", type=int, default=DEV_SEED_BASE)
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 2))
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from registry import EXTRA, IMPORT_ERRORS

    names = [x for x in a.policies.split(",") if x]
    unknown = [n for n in names if n not in EXTRA and n not in (
        "gated_deployment", "discern_style", "SMCS+retain-incumbent", "model_picker_adapter",
        "model_selector_causal", "online_llm_picker", "xu_acquisition_only", "cams_adapter",
        "variance_min_ipw", "P7s_settled", "CONTROL_never_switch", "economic_replacement")]
    if unknown:
        sys.exit(f"unknown policies {unknown}; import errors: {IMPORT_ERRORS}")
    regimes = [x for x in a.regimes.split(",") if x]
    jobs = []
    for r in regimes:
        if a.kind == "synthetic":
            jobs += [("synthetic", r, 0, s, a.seed_base, names) for s in range(a.seeds)]
        else:
            K = np.load(LOSS_DIR / f"{r}.npz")["l0"].shape[0]
            jobs += [("real", r, e, s, a.seed_base, names) for e in range(K) for s in range(a.seeds)]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(out / "records.jsonl", "w") as f, mp.Pool(a.workers) as pool:
        for rows in pool.imap_unordered(_job, jobs, chunksize=2):
            for row in rows:
                f.write(json.dumps(row) + "\n")
    srcs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            for p in sorted(HERE.glob("*.py"))}
    manifest = {"argv": vars(a), "contract": CONTRACT, "git": _git_rev(), "sources": srcs,
                "import_errors": IMPORT_ERRORS, "n_jobs": len(jobs),
                "seconds": round(time.time() - t0, 1)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"done {len(jobs)} jobs in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
