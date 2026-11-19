"""Phase 2 (Addendum A): candidates P1..P30 in order; screen on lag-1 autocorrelation, then fit/G1/G2/evaluate.

Usage: uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/run_phase2.py [first [last]]
Appends to results/attempts_phase2.jsonl, per-candidate results/p<NN>_*.json. Resumable. Stops at 10 positives
under the any-cell rule (rho > 1e-3 at any delay-1 grid cell, G1 and G2 passed) or when the list is exhausted.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evaluate as ev  # noqa: E402
import fetch_p as fp  # noqa: E402
import fit as ft  # noqa: E402
import numpy as np  # noqa: E402

ROOT = HERE.parents[3]
RES = ROOT / "docs/paper4_continuation/rbdp/real_data/results"
ATT = RES / "attempts_phase2.jsonl"
R1_CUT = -0.15
RHO_POS = 1e-3
TARGET = 10
TINY_VOI = 0.05  # flag when C0 - U_iid at a positive cell is below this (absolute)


def lag1(x):
    x = np.asarray(x, float)
    if x.std() == 0:
        return float("nan")
    return float(np.corrcoef(x[:-1], x[1:])[0, 1])


def family(n):
    return "geyser" if n in (23, 24) else "exchange_tick" if n <= 22 else "exchange_1s_kline"


def process(n):
    t0 = time.perf_counter()
    rec = dict(n_cand=n, id=fp.pid(n), family=family(n), started=time.strftime("%Y-%m-%dT%H:%M:%S"))
    f = fp.fetch(n)
    rec["fetch"] = f
    if not f["ok"]:
        rec.update(outcome="fetch failed", reason=f["error"])
        return rec
    x = np.loadtxt(fp.F.RAW / fp.pid(n) / "stream.csv", skiprows=1, dtype=int)
    r1 = lag1(x)
    rec.update(n=int(len(x)), n_ones=int(x.sum()), binarisation=f["rule"], r1=r1)
    if not (r1 <= R1_CUT):
        rec.update(outcome="screened out", reason=f"r1={r1:.4f} > {R1_CUT}")
        return rec
    t1 = time.perf_counter()
    fit = ft.fit_hmm(x)
    rec["fit"] = fit
    rec["eigenvalue"] = 1 - fit["t01"] - fit["t10"]
    rec["g1"] = ft.gate_g1(x, full_fit=fit)
    rec["g2"] = ft.gate_g2(fit)
    rec["time_fit_s"] = time.perf_counter() - t1
    g1, g2 = rec["g1"]["pass_"], rec["g2"]["pass_"]
    flags = []
    fb = rec["g2"]["at_bounds"]
    if any(fb.values()):
        flags.append("param_at_bound:" + ",".join(k for k, v in fb.items() if v))
    if fit["e0"] < 0.02 or fit["e1"] > 0.98:
        flags.append("near_deterministic_emission")
    if fit["t01"] + fit["t10"] > 1 and (fit["t01"] > 0.9 or fit["t10"] > 0.9):
        flags.append("t01+t10>1_with_t_near_1")
    if g2:
        sp = ft.solver_params(fit)
        rec["solver_params"] = sp
        cells = ev.eval_chain(sp, delay1=True, delay2=False)
        rec["cells_d1"] = cells
        ok = [c for c in cells if c["status"] == "ok"]
        prim = next((c for c in ok if (c["T"], c["B"]) == ev.PRIMARY), None)
        rec["rho_primary"] = prim["rho_Gamma"] if prim else None
        rec["risk_iid_policy_primary"] = prim["risk_causal_of_iid_policy"] if prim else None
        if ok:
            best = max(ok, key=lambda c: c["rho_Gamma"])
            rec["best_cell"] = dict(T=best["T"], B=best["B"], rho=best["rho_Gamma"], gamma=best["Gamma"], C0=best["C0"],
                                    U_iid=best["U_iid"], U_causal=best["U_causal"], C0_minus_Uiid=best["C0"] - best["U_iid"],
                                    risk_iid_policy=best["risk_causal_of_iid_policy"])
            rec["rho_max"] = best["rho_Gamma"]
            pos_cells = [c for c in ok if c["rho_Gamma"] > RHO_POS]
            rec["positive_cells"] = [dict(T=c["T"], B=c["B"], rho=c["rho_Gamma"], C0_minus_Uiid=c["C0"] - c["U_iid"],
                                          risk_iid_policy=c["risk_causal_of_iid_policy"]) for c in pos_cells]
            if any(c.get("degenerate_zero_voi") for c in ok):
                flags.append("zero_voi_cells:" + str(sum(1 for c in ok if c.get("degenerate_zero_voi"))))
            if pos_cells and min(c["C0"] - c["U_iid"] for c in pos_cells) < TINY_VOI:
                flags.append(f"tiny_C0_minus_Uiid(<{TINY_VOI}) at a positive cell")
        else:
            rec["rho_max"] = None
            rec["positive_cells"] = []
        rec["positive_primary_rule"] = bool(g1 and rec["rho_primary"] is not None and rec["rho_primary"] > RHO_POS)
        rec["positive_any_cell_rule"] = bool(g1 and rec["positive_cells"])
        rec["substantial"] = bool(rec["rho_max"] is not None and rec["rho_max"] >= 0.05 and g1)
        if not g1:
            rec.update(outcome="evaluated, G1 failed (not applicable)", reason="G1 failed; numbers informational")
        elif rec["positive_any_cell_rule"]:
            rec.update(outcome="positive", reason=f"rho_max={rec['rho_max']:.6g} at T={best['T']},B={best['B']}")
            rec["cells_d2"] = ev.eval_chain(sp, delay1=False, delay2=True)
        elif not ok:
            rec.update(outcome="evaluation failed", reason=str([c["status"] for c in cells]))
        else:
            rec.update(outcome="null", reason="rho <= 1e-3 at all 8 cells")
    else:
        rec.update(outcome="evaluated, G2 failed (not applicable)", reason=f"G2 failed: {rec['g2']}",
                   positive_primary_rule=False, positive_any_cell_rule=False)
    rec["degeneracy_flags"] = flags
    rec["runtime_s"] = time.perf_counter() - t0
    return rec


def load_done():
    out = {}
    if ATT.exists():
        for line in ATT.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["n_cand"]] = r
    return out


def tally(done):
    v = list(done.values())
    return " | ".join(f"{k}={c}" for k, c in dict(
        attempted=len(v), fetched=sum(r["outcome"] != "fetch failed" for r in v),
        screened_out=sum(r["outcome"] == "screened out" for r in v),
        evaluated=sum("fit" in r for r in v),
        passed_gates=sum(bool(r.get("g1", {}).get("pass_") and r.get("g2", {}).get("pass_")) for r in v),
        pos_any=sum(bool(r.get("positive_any_cell_rule")) for r in v),
        pos_primary=sum(bool(r.get("positive_primary_rule")) for r in v),
        substantial=sum(bool(r.get("substantial") and r.get("positive_any_cell_rule")) for r in v),
        fetch_failed=sum(r["outcome"] == "fetch failed" for r in v)).items())


def main():
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    last = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    RES.mkdir(parents=True, exist_ok=True)
    done = load_done()
    for n in range(first, last + 1):
        if sum(bool(r.get("positive_any_cell_rule")) for r in done.values()) >= TARGET:
            print("10 positives (any-cell rule) reached; stopping")
            break
        if n in done:
            continue
        print(f"[P{n}] {fp.pid(n)}", flush=True)
        rec = process(n)
        (RES / f"{rec['id']}.json").write_text(json.dumps(rec, indent=1, default=str))
        with open(ATT, "a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        done[n] = rec
        print(f"   -> {rec['outcome']}: {rec.get('reason')} r1={rec.get('r1')} ({rec.get('runtime_s', 0):.1f}s)", flush=True)
        print("   TALLY", tally(done), flush=True)
    print("FINAL", tally(done))


if __name__ == "__main__":
    main()
