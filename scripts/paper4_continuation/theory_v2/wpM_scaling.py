"""WP-M scaling: certified rho_Gamma vs horizon T for symmetric stationary anti-persistent chains.

rho_Gamma = Gamma / (C0 - V*_IID), C0 = never-query/never-promote cost = sum_t P_A(Y_t=1).
Not confirmatory.  C0 = T/2 (stationary symmetric).  Larger T in a (t,d,k,alpha,B) group is skipped once a smaller T timed out.  Each gamma_cell call runs in its own process with a hard timeout.
"""
from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
from fractions import Fraction as F

sys.set_int_max_str_digits(0)  # exact rationals can have >4300 digits
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "paper4_continuation", "theory_C"))
OUT = os.path.join(ROOT, "outputs/paper4_theory_v2/wpM_scaling_v1.json")
PARTIAL = os.environ.get("WPM_PARTIAL", "/tmp/wpM_partial.jsonl")
TIMEOUT = 900
WALL = float(os.environ.get("WPM_WALL_S", 4 * 3600))
NPROC = 2  # hard limit from user (machine load)
ALPHAS = [F(1, 20), F(1, 10), F(1, 4)]
COMPACT = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_scaling_v1_compact.json")


def build_cells():
    cells = []
    for t in (F(2, 3), F(3, 4), F(9, 10)):
        for d in (1, 3):
            for k in (F(0), F(1, 50)):
                for a in ALPHAS:
                    for B in (1, 2, 3, 4):
                        for T in range(B + d, (16 if B <= 2 else 12) + 1):
                            cells.append(dict(T=T, B=B, alpha=a, t01=t, t10=t, e0=F(1, 10), e1=F(9, 10), d=d,
                                              prior=F(1, 2), c=F(0), k=k))
    pri = lambda c: (c["k"] != 0, c["d"] == 3, c["B"] > 2, c["alpha"] == F(1, 4), c["T"], c["t01"], c["B"], c["alpha"])
    if os.environ.get("WPM_PRI") == "v2":
        # Lead re-prioritisation (2026-11-11 ~01:50): rho is alpha-free in the data, so after the k=0, d=1, B<=2 cells,
        # run B=3,4 at alpha=1/10 for the faster-mixing chains, then the d=3 parity check, then everything else.
        def stage(c):
            base = c["k"] == 0 and c["d"] == 1
            if base and c["B"] <= 2 and c["alpha"] != F(1, 4):
                return 0
            if base and c["B"] > 2 and c["alpha"] == F(1, 10) and c["t01"] != F(9, 10):
                return 1
            if base and c["B"] > 2 and c["alpha"] == F(1, 10):
                return 2
            if c["k"] == 0 and c["d"] == 3 and c["B"] <= 2 and c["alpha"] == F(1, 10):
                return 3
            return 4
        pri = lambda c: (stage(c), c["T"], c["t01"], c["B"], c["alpha"], c["k"] != 0, c["d"])
    return sorted(cells, key=pri)


def key(c):
    return (str(c["t01"]), c["d"], str(c["k"]), str(c["alpha"]), c["B"], c["T"])


def gkey(c):
    return key(c)[:5]


def c0(T, t01, t10, e0, e1, prior):
    p, s = F(prior), F(0)
    for _ in range(T):
        p = p * (1 - t10) + (1 - p) * t01
        s += e0 + (e1 - e0) * p
    return s


def worker(conn, kw):
    from gamma_lib import gamma_cell
    try:
        conn.send(("ok", gamma_cell(**kw)))
    except Exception as e:  # noqa: BLE001
        conn.send(("error", repr(e)))
    conn.close()


def finish(cell, status, res, rt):
    rec = {k: str(v) if isinstance(v, F) else v for k, v in cell.items()}
    rec["C0"] = str(c0(cell["T"], cell["t01"], cell["t10"], cell["e0"], cell["e1"], cell["prior"]))
    rec["status"], rec["runtime_s"] = status, rt
    if status == "ok":
        C0 = F(rec["C0"])
        Lq, Uq, Lc, Uc = (F(res[k]) for k in ("L_IID", "U_IID", "L_causal", "U_causal"))
        glo, ghi = F(res["Gamma_lo"]), F(res["Gamma_hi"])
        rec.update(res_V_causal_source=res["V_causal_source"], iid_opt_causal_safe=res["iid_opt_causal_safe"])
        rec["V_IID"] = [str(Lq), str(Uq)]
        rec["V_causal"] = [str(Lc), str(Uc)]
        rec["Gamma"] = [str(glo), str(ghi)]
        gmid, vmid = (glo + ghi) / 2, (Lq + Uq) / 2
        rec["Gamma_mid_f"] = float(gmid)
        rec["Gamma_f"] = [float(glo), float(ghi)]
        rec["VOI_mid_f"] = float(C0 - vmid)
        rec["VOI_interval_f"] = [float(C0 - Uq), float(C0 - Lq)]
        if C0 - vmid > F(1, 10**9):
            rec["rho_mid"] = float(gmid / (C0 - vmid))
            if C0 - Uq > 0:
                rec["rho_interval"] = [float(max(glo, F(0)) / (C0 - Lq)), float(ghi / (C0 - Uq))]
        else:
            rec["rho_mid"] = None
    return rec


def main():
    here = os.path.abspath(__file__)
    sha = hashlib.sha256(open(here, "rb").read()).hexdigest()
    if os.path.exists(OUT) or os.path.exists(COMPACT):
        sys.exit("refusing to overwrite output")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cells = build_cells()
    print(f"{len(cells)} cells; sha256 {sha}", flush=True)
    t_start = time.time()
    ctx = mp.get_context("spawn")
    running, results, idx = [], [], 0
    done, dead = set(), set()
    if os.path.exists(PARTIAL):
        for line in open(PARTIAL):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r["status"] in ("ok", "skipped_timeout", "skipped_after_timeout"):
                results.append(r)
                done.add((str(F(r["t01"])), r["d"], str(F(r["k"])), str(F(r["alpha"])), r["B"], r["T"]))
                if r["status"] == "skipped_timeout":
                    dead.add((str(F(r["t01"])), r["d"], str(F(r["k"])), str(F(r["alpha"])), r["B"], r["T"]))
    cells = [c for c in cells if key(c) not in done]
    # (group, T) of timeouts; any cell with larger T in the same group is skipped
    dead_by_group = {}
    for k_ in dead:
        dead_by_group[k_[:5]] = min(dead_by_group.get(k_[:5], 99), k_[5])
    print(f"resumed {len(results)} cells; {len(cells)} remaining", flush=True)
    pf = open(PARTIAL, "a")

    def record(rec):
        results.append(rec); pf.write(json.dumps(rec) + "\n"); pf.flush()
        if len(results) % 25 == 0:
            print(len(results), "done;", sum(r["status"] != "ok" for r in results), "non-ok",
                  f"{time.time()-t_start:.0f}s", flush=True)

    while (idx < len(cells) and time.time() - t_start < WALL) or running:
        while len(running) < NPROC and idx < len(cells) and time.time() - t_start < WALL:
            c = cells[idx]; idx += 1
            if gkey(c) in dead_by_group and c["T"] > dead_by_group[gkey(c)]:
                record(finish(c, "skipped_after_timeout", None, 0.0)); continue
            kw = dict(T=c["T"], B=c["B"], d=c["d"], t01=c["t01"], t10=c["t10"], e0=c["e0"], e1=c["e1"],
                      prior=c["prior"], c=c["c"], k=c["k"], alpha=c["alpha"])
            pr, ch = ctx.Pipe(duplex=False)
            p = ctx.Process(target=worker, args=(ch, kw)); p.start(); ch.close()
            running.append((p, pr, c, time.time()))
        time.sleep(0.2)
        for item in list(running):
            p, pr, c, t0 = item
            rt = time.time() - t0
            if pr.poll():
                st, res = pr.recv(); p.join()
                rec = finish(c, st, res if st == "ok" else None, rt)
                if st != "ok":
                    rec["error"] = res
            elif rt > TIMEOUT:
                p.kill(); p.join()
                rec = finish(c, "skipped_timeout", None, rt)
                dead_by_group[gkey(c)] = min(dead_by_group.get(gkey(c), 99), c["T"])
            elif not p.is_alive():
                rec = finish(c, "error", None, rt); rec["error"] = "process died"
            else:
                continue
            running.remove(item); record(rec)
    for c in cells[idx:]:
        results.append(finish(c, "not_run_wall_budget", None, 0.0))
    payload = dict(script=here, script_sha256=sha, timeout_s=TIMEOUT, wall_budget_s=WALL,
                   elapsed_s_last_session=time.time() - t_start, nproc=NPROC, n_cells=len(results), cells=results,
                   note="descriptive numerics; certified intervals from gamma_cell")
    with open(OUT, "x") as fh:
        json.dump(payload, fh, indent=1)
    keep = ["t01", "d", "k", "alpha", "B", "T", "status", "runtime_s", "Gamma_f", "Gamma_mid_f", "VOI_interval_f",
            "VOI_mid_f", "rho_mid", "rho_interval"]
    comp = dict(script_sha256=sha, wall_budget_s=WALL, timeout_s=TIMEOUT,
                cells=[{k_: r.get(k_) for k_ in keep} | {"C0": float(F(r["C0"]))} for r in results])
    with open(COMPACT, "x") as fh:
        json.dump(comp, fh)
    print("wrote", OUT, COMPACT)


if __name__ == "__main__":
    main()
