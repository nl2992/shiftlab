"""Run the real-chain protocol over candidates 1..30 in order (resumable).

Usage: uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/run_all.py [first [last]]
Appends one JSON line per candidate to docs/paper4_continuation/rbdp/real_data/results/attempts.jsonl and writes
results/<id>.json. Stops after 10 candidates with outcome "positive premium" or when the list is exhausted.
Outcomes: positive (rho_Gamma > 1e-3 at T=32, B=3, delay 1, G1 and G2 passed), null (gates passed, rho <= 1e-3),
not applicable (G1 or G2 failed), fetch failed, evaluation failed (primary cell did not solve).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evaluate as ev  # noqa: E402
import fetch as fe  # noqa: E402
import fit as ft  # noqa: E402
import numpy as np  # noqa: E402

ROOT = HERE.parents[3]
RES = ROOT / "docs/paper4_continuation/rbdp/real_data/results"
ATT = RES / "attempts.jsonl"
RHO_POS = 1e-3
RHO_SUB = 0.05
N_CAND = 30
TARGET = 10


def load_done() -> dict:
    out = {}
    if ATT.exists():
        for line in ATT.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["n_cand"]] = r
    return out


def tally(done: dict) -> str:
    c = {"attempted": len(done)}
    o = [r["outcome"] for r in done.values()]
    c["passed_gates"] = sum(1 for r in done.values() if r.get("g1", {}).get("pass_") and r.get("g2", {}).get("pass_"))
    c["positive"] = o.count("positive")
    c["substantial"] = sum(1 for r in done.values() if r["outcome"] == "positive" and r["rho_primary"] >= RHO_SUB)
    c["null"] = o.count("null")
    c["not_applicable"] = o.count("not applicable")
    c["fetch_failed"] = o.count("fetch failed")
    c["eval_failed"] = o.count("evaluation failed")
    return " | ".join(f"{k}={v}" for k, v in c.items())


def process(n: int) -> dict:
    t0 = time.perf_counter()
    rec = dict(n_cand=n, id=fe.cid(n), started=time.strftime("%Y-%m-%dT%H:%M:%S"))
    f = fe.fetch(n)
    rec["fetch"] = f
    if not f["ok"]:
        rec.update(outcome="fetch failed", reason=f["error"])
        return rec
    x = np.loadtxt(fe.RAW / fe.cid(n) / "stream.csv", skiprows=1, dtype=int)
    rec.update(n=int(len(x)), n_ones=int(x.sum()), binarisation=f["rule"])
    t1 = time.perf_counter()
    fit = ft.fit_hmm(x)
    rec["fit"] = fit
    rec["g1"] = ft.gate_g1(x, full_fit=fit)
    rec["g2"] = ft.gate_g2(fit)
    rec["time_fit_s"] = time.perf_counter() - t1
    g1, g2 = rec["g1"]["pass_"], rec["g2"]["pass_"]
    cells = []
    if g2:
        sp = ft.solver_params(fit)
        rec["solver_params"] = sp
        positive_possible = g1
        cells = ev.eval_chain(sp, delay1=True, delay2=False)
        rec["cells_d1"] = cells
        prim = next((c for c in cells if c["delay"] == 1 and (c["T"], c["B"]) == ev.PRIMARY), None)
        if prim and prim["status"] == "ok":
            rec["rho_primary"] = prim["rho_Gamma"]
            rec["risk_iid_policy_primary"] = prim["risk_causal_of_iid_policy"]
            rec["gamma_primary"] = prim["Gamma"]
            rec["C0_primary"] = prim["C0"]
            rec["U_causal_primary"] = prim["U_causal"]
            rec["U_iid_primary"] = prim["U_iid"]
        else:
            rec["rho_primary"] = None
        if not positive_possible:
            rec.update(outcome="not applicable", reason="G1 failed (primary-cell numbers informational only)")
        elif rec["rho_primary"] is None:
            rec.update(outcome="evaluation failed", reason=str(prim["status"] if prim else "no primary cell"))
        elif rec["rho_primary"] > RHO_POS:
            rec.update(outcome="positive", reason=f"rho_Gamma={rec['rho_primary']:.6g} > 1e-3")
            rec["cells_d2"] = ev.eval_chain(sp, delay1=False, delay2=True)
        else:
            rec.update(outcome="null", reason=f"rho_Gamma={rec['rho_primary']:.3g} <= 1e-3")
    else:
        rec.update(outcome="not applicable",
                   reason="G2 failed" + ("" if g1 else " and G1 failed") + f" ({rec['g2']})")
    rec["runtime_s"] = time.perf_counter() - t0
    return rec


def main() -> None:
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    last = int(sys.argv[2]) if len(sys.argv) > 2 else N_CAND
    RES.mkdir(parents=True, exist_ok=True)
    done = load_done()
    for n in range(first, last + 1):
        if sum(1 for r in done.values() if r["outcome"] == "positive") >= TARGET:
            print("10 positives reached; stopping")
            break
        if n in done:
            continue
        print(f"[{n}/{N_CAND}] {fe.cid(n)}", flush=True)
        rec = process(n)
        (RES / f"{rec['id']}.json").write_text(json.dumps(rec, indent=1, default=str))
        with open(ATT, "a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        done[n] = rec
        print(f"   -> {rec['outcome']}: {rec.get('reason')}  ({rec.get('runtime_s', 0):.1f}s)", flush=True)
        print("   TALLY", tally(done), flush=True)
    print("FINAL", tally(done))


if __name__ == "__main__":
    main()
