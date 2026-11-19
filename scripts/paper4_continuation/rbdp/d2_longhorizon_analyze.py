"""Summarise the delay-2 long-horizon study: tables to stdout, d2_longhorizon_summary.json to disk.

Run: uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_analyze.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RES = ROOT / "docs/paper4_continuation/rbdp/results"
TOL = 1e-9


def load(p: Path) -> list[dict]:
    return [json.loads(line) for line in open(p)] if p.exists() else []


def fmt(x, nd=4):
    return "-" if x is None else f"{x:.{nd}f}"


def main() -> None:
    cells = load(RES / "d2_longhorizon_cells.jsonl")
    sens = load(RES / "d2_longhorizon_sens.jsonl")
    d1 = {}
    for r in load(RES / "e2e3_fast_cells.jsonl"):
        if r["kind"] == "E3" and r["e"] == "1/10" and r["n_beta"] == 401:
            d1[(r["t"], r["B"], r["T"])] = r["rho_Gamma"]
    ok = [c for c in cells if c["status"] == "ok"]
    bad = [c for c in cells if c["status"] != "ok"]
    for c in ok:
        c["rho_Gamma_delay1"] = d1.get((c["t"], c["B"], c["T"]))
    flags = []
    for c in ok:
        if c["V_causal"] < c["V_iid"] - TOL:
            flags.append(dict(cell=[c["t"], c["B"], c["T"]], issue="V_causal < V_iid - 1e-9", gap=c["V_causal"] - c["V_iid"]))
        if c["risk_causal_of_causal_policy"] > 0.1 + TOL:
            flags.append(dict(cell=[c["t"], c["B"], c["T"]], issue="causal-policy causal risk > alpha", risk=c["risk_causal_of_causal_policy"]))
    series = defaultdict(list)
    for c in sorted(ok, key=lambda c: c["T"]):
        series[f"t={c['t']},B={c['B']}"].append(dict(T=c["T"], rho2=c["rho_Gamma"], rho1=c["rho_Gamma_delay1"], Gamma=c["Gamma"],
                                                      risk_iid_policy=c["risk_causal_of_iid_policy"]))
    # sensitivity
    sg = defaultdict(dict)
    for r in sens:
        if r["status"] == "ok":
            sg[(r["t"], r["B"], r["T"])][("reach" if r["belief_grid"] == "reach" else r["n_beta"])] = r
    for c in ok:
        if c["T"] in (32, 64) and c["B"] in (2, 3) and c["n_beta"] == 401:
            sg[(c["t"], c["B"], c["T"])].setdefault(401, c)
    sens_rows = []
    for k, v in sorted(sg.items()):
        row = dict(t=k[0], B=k[1], T=k[2])
        for g, r in v.items():
            row[str(g)] = dict(V_causal=r["V_causal"], V_iid=r["V_iid"], rho=r["rho_Gamma"], Gamma=r["Gamma"])
        if 201 in v and 401 in v:
            row["d401_201"] = dict(V_causal=v[401]["V_causal"] - v[201]["V_causal"], V_iid=v[401]["V_iid"] - v[201]["V_iid"],
                                   rho=v[401]["rho_Gamma"] - v[201]["rho_Gamma"])
        if 801 in v and 401 in v:
            row["d801_401"] = dict(V_causal=v[801]["V_causal"] - v[401]["V_causal"], V_iid=v[801]["V_iid"] - v[401]["V_iid"],
                                   rho=v[801]["rho_Gamma"] - v[401]["rho_Gamma"])
        if "reach" in v and 401 in v:
            row["d401_reach"] = dict(V_causal=v[401]["V_causal"] - v["reach"]["V_causal"], V_iid=v[401]["V_iid"] - v["reach"]["V_iid"],
                                     rho=v[401]["rho_Gamma"] - v["reach"]["rho_Gamma"])
        sens_rows.append(row)
    summary = dict(
        n_cells=len(cells), n_ok=len(ok), not_ok=[dict(t=c["t"], B=c["B"], T=c["T"], status=c["status"]) for c in bad],
        max_risk_causal_of_causal_policy=max((c["risk_causal_of_causal_policy"] for c in ok), default=None),
        max_risk_causal_of_iid_policy=max((c["risk_causal_of_iid_policy"] for c in ok), default=None),
        flags=flags, series=series, sensitivity=sens_rows,
        sens_not_ok=[dict(t=r["t"], B=r["B"], T=r["T"], grid=r["belief_grid"], n_beta=r["n_beta"], status=r["status"]) for r in sens if r["status"] != "ok"],
        total_solver_seconds=sum(c[m].get("time_total", 0) for c in ok for m in ("causal", "iid")),
        max_cell_wall_s=max((c["causal"]["wall_s"] + c["iid"]["wall_s"] for c in ok), default=None),
    )
    json.dump(summary, open(RES / "d2_longhorizon_summary.json", "w"), indent=1)

    print("| t | B | T | rho_G d2 | rho_G d1 | Gamma d2 | V_causal | V_iid | C0 | causal risk of IID policy | causal risk of causal policy | wall s (c+i) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in sorted(cells, key=lambda c: (c["t"], c["B"], c["T"])):
        if c["status"] != "ok":
            print(f"| {c['t']} | {c['B']} | {c['T']} | {c['status']} | {fmt(d1.get((c['t'], c['B'], c['T'])))} | | | | | | | |")
            continue
        print(f"| {c['t']} | {c['B']} | {c['T']} | {fmt(c['rho_Gamma'])} | {fmt(c['rho_Gamma_delay1'])} | {c['Gamma']:.3e} | {c['V_causal']:.6f} | "
              f"{c['V_iid']:.6f} | {c['C0']:.3f} | {c['risk_causal_of_iid_policy']:.4f} | {c['risk_causal_of_causal_policy']:.4f} | "
              f"{c['causal']['wall_s'] + c['iid']['wall_s']:.0f} |")
    print("\nflags:", flags)
    print("max causal-policy risk:", summary["max_risk_causal_of_causal_policy"])
    print("not ok:", summary["not_ok"], summary["sens_not_ok"])
    print("\nsensitivity:")
    for r in sens_rows:
        print(json.dumps(r))


if __name__ == "__main__":
    main()
