"""WP-C2 descriptive diagnostic: causal-safety premium Gamma relative to value of information.

rho_Gamma = Gamma / (C0 - V*_IID), C0 = never-query/never-promote cost = sum_t P_A(Y_t=1).
Not confirmatory.  Each gamma_cell call runs in its own process with a hard timeout.
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
OUT = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpC2_relative_premium_v1.json")
PARTIAL = os.environ.get("WPC2_PARTIAL", "/tmp/wpC2_partial.jsonl")
TIMEOUT = 600
WALL = float(os.environ.get("WPC2_WALL_S", 2.5 * 3600))
NPROC = 3  # reduced from 6 on user request (machine load); run resumed from partial file
ALPHAS = [F(1, 20), F(1, 10), F(1, 4), F(1, 2)]


def configs():
    out = []
    for t in (F(1, 10), F(1, 4)):
        for e in ((F(1, 100), F(99, 100)), (F(1, 10), F(9, 10))):
            for d in (1, 2):
                out.append(dict(family="F_persist", t01=t, t10=t, e0=e[0], e1=e[1], d=d, prior=F(1, 2), c=F(0), k=F(0)))
    for t in (F(3, 4), F(9, 10)):
        for k in (F(0), F(1, 50)):
            out.append(dict(family="F_anti", t01=t, t10=t, e0=F(1, 10), e1=F(9, 10), d=1, prior=F(1, 2), c=F(0), k=k))
    out.append(dict(family="F_coin", t01=F(1, 2), t10=F(1, 10), e0=F(1, 10), e1=F(3, 5), d=1, prior=F(0), c=F(0), k=F(0)))
    return out


def c0(T, t01, t10, e0, e1, prior):
    # model propagates the prior (regime at time 0) one step before the first emission
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


def build_cells():
    cells = []
    for ci, cfg in enumerate(configs()):
        for T in range(4, 11):
            for B in range(1, 7):
                if B > T - cfg["d"]:
                    continue
                for a in ALPHAS:
                    cells.append(dict(cfg_id=ci, T=T, B=B, alpha=a, **cfg))
    pri = lambda c: (0 if (c["alpha"] in (F(1, 10), F(1, 4)) and c["T"] <= 8) else 1, c["T"], c["B"], c["cfg_id"])
    return sorted(cells, key=pri)


def finish(cell, status, res, rt):
    rec = {k: str(v) if isinstance(v, F) else v for k, v in cell.items()}
    rec["C0"] = str(c0(cell["T"], cell["t01"], cell["t10"], cell["e0"], cell["e1"], cell["prior"]))
    rec["C0_f"] = float(F(rec["C0"]))
    rec["status"], rec["runtime_s"] = status, rt
    if status == "ok":
        C0 = F(rec["C0"])
        Lq, Uq, Lc, Uc = (F(res[k]) for k in ("L_IID", "U_IID", "L_causal", "U_causal"))
        glo, ghi = F(res["Gamma_lo"]), F(res["Gamma_hi"])
        rec.update(res_V_causal_source=res["V_causal_source"], iid_opt_causal_safe=res["iid_opt_causal_safe"])
        rec["V_IID"] = [str(Lq), str(Uq)]
        rec["V_causal"] = [str(Lc), str(Uc)]
        rec["Gamma"] = [str(glo), str(ghi)]
        rec["V_IID_f"] = [float(Lq), float(Uq)]
        rec["V_causal_f"] = [float(Lc), float(Uc)]
        rec["Gamma_f"] = [float(glo), float(ghi)]
        gmid, vmid = (glo + ghi) / 2, (Lq + Uq) / 2
        rec["Gamma_mid_f"] = float(gmid)
        rec["VOI_mid_f"] = float(C0 - vmid)
        rec["VOI_interval_f"] = [float(C0 - Uq), float(C0 - Lq)]
        if C0 - vmid > F(1, 10**9):
            rec["rho_mid"] = float(gmid / (C0 - vmid))
            if C0 - Uq > 0:
                rec["rho_interval"] = [float(max(glo, F(0)) / (C0 - Lq)), float(ghi / (C0 - Uq))]
        else:
            rec["rho_mid"] = None  # no value of information (V_IID ~ C0)
    return rec


def main():
    here = os.path.abspath(__file__)
    sha = hashlib.sha256(open(here, "rb").read()).hexdigest()
    if os.path.exists(OUT):
        sys.exit(f"refusing to overwrite {OUT}")
    cells = build_cells()
    print(f"{len(cells)} cells; sha256 {sha}", flush=True)
    t_start = time.time()
    ctx = mp.get_context("spawn")
    running, results, idx = [], [], 0
    done = set()
    if os.path.exists(PARTIAL):  # resume: keep completed/timed-out cells, rerun errors
        for line in open(PARTIAL):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r["status"] in ("ok", "skipped_timeout"):
                results.append(r); done.add((r["cfg_id"], r["T"], r["B"], r["alpha"]))
    cells = [c for c in cells if (c["cfg_id"], c["T"], c["B"], str(c["alpha"])) not in done]
    print(f"resumed {len(results)} cells; {len(cells)} remaining", flush=True)
    pf = open(PARTIAL, "a")
    while (idx < len(cells) and time.time() - t_start < WALL) or running:
        while len(running) < NPROC and idx < len(cells) and time.time() - t_start < WALL:
            c = cells[idx]; idx += 1
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
            elif not p.is_alive():
                rec = finish(c, "error", None, rt); rec["error"] = "process died"
            else:
                continue
            running.remove(item); results.append(rec)
            pf.write(json.dumps(rec) + "\n"); pf.flush()
            if len(results) % 25 == 0:
                print(len(results), "done;", sum(r["status"] != "ok" for r in results), "non-ok", flush=True)
    for c in cells[idx:]:
        rec = finish(c, "not_run_wall_budget", None, 0.0)
        results.append(rec)
    payload = dict(script=here, script_sha256=sha, timeout_s=TIMEOUT, wall_budget_s=WALL,
                   elapsed_s_last_session=time.time() - t_start, nproc_last_session=NPROC, resumed=True, n_cells=len(results), cells=results,
                   note="descriptive diagnostic; C0 verified against gamma_cell at alpha=0 on 3 spot cells")
    with open(OUT, "x") as fh:
        json.dump(payload, fh, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
