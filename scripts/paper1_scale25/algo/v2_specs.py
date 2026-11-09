# ruff: noqa
"""v2 candidate ledger (every candidate that is run is listed here and in the ledger CSV).

    python v2_specs.py   -> OUT/specs_v2.json, docs/paper1_scale25/algo/V2_LEDGER.csv
Base for every candidate is EQ+cut (arm R, cutoff 1100) + E48[s0] + F60[s0] (the frozen pair) unless the
description says otherwise; the frozen v1 is not modified. Parameters are as shown (all other module
parameters at the registered defaults).
"""

import csv
import json

import s25_common as sc

E48S = {"id": "E48", "setting": 0}
F60S = {"id": "F60", "setting": 0}


def e48(**p):
    return {"id": "E48", "setting": 0, "params": p}


def f60(**p):
    return {"id": "F60", "setting": 0, "params": p}


C = []  # (name, family, description, modules)


def add(name, fam, desc, mods):
    C.append((name, fam, desc, mods))


# A: re-tuned parameters of the frozen modules (not new mechanism; calibrates the reference)
for d, lk, hz in [
    (0.75, 50, 0.002),
    (1.0, 50, 0.002),
    (0.5, 25, 0.002),
    (0.5, 100, 0.002),
    (0.5, 50, 0.001),
    (0.5, 50, 0.004),
]:
    add(
        f"V2A_E48_d{d}_l{lk}_h{hz}",
        "A_retune",
        f"E48 arrival_discount={d} lookahead={lk} hazard={hz} + F60[s0]",
        [e48(arrival_discount=d, lookahead=lk, hazard=hz), F60S],
    )
for b, hor, hz in [(3, 100, 0.002), (2, 150, 0.002), (2, 100, 0.001), (2, 100, 0.004)]:
    add(
        f"V2A_F60_b{b}_H{hor}_h{hz}",
        "A_retune",
        f"F60 bundle={b} horizon={hor} hazard={hz} + E48[s0]",
        [E48S, f60(bundle=b, horizon=hor, hazard=hz)],
    )
# B: hazard-adaptive modules (hazard scaled by recent-vs-overall label disagreement)
for k in (1.0, 2.0):
    add(
        f"V2B_E48A_k{k}",
        "B_hazard_adaptive",
        f"E48 with adaptive hazard kappa={k} + F60[s0]",
        [{"id": "E48A", "setting": 0, "params": {"kappa": k}}, F60S],
    )
    add(
        f"V2B_F60A_k{k}",
        "B_hazard_adaptive",
        f"E48[s0] + F60 with adaptive hazard kappa={k}",
        [E48S, {"id": "F60A", "setting": 0, "params": {"kappa": k}}],
    )
    add(
        f"V2B_both_k{k}",
        "B_hazard_adaptive",
        f"E48A + F60A adaptive hazard kappa={k}",
        [
            {"id": "E48A", "setting": 0, "params": {"kappa": k}},
            {"id": "F60A", "setting": 0, "params": {"kappa": k}},
        ],
    )
# C: early adoption under the change-hazard posterior
for g2, m in [(0.4, 1.0), (0.5, 1.0), (0.4, 1.5), (0.5, 1.5)]:
    add(
        f"V2C_EAP_g{g2}_m{m}",
        "C_early_adoption",
        f"pair + EAP quantile={g2} mult={m}",
        [E48S, F60S, {"id": "EAP", "params": {"gamma2": g2, "mult": m}}],
    )
add(
    "V2C_EAP_alone_g0.4",
    "C_early_adoption",
    "EQ+cut + EAP quantile=0.4 (no E48/F60)",
    [{"id": "EAP", "params": {"gamma2": 0.4, "mult": 1.0}}],
)
# D: one-step DP (wait for in-flight labels vs adopt now)
for m in (1.0, 1.5):
    add(
        f"V2D_DPW_m{m}",
        "D_dp_wait",
        f"pair + DPW one-step optimal stopping mult={m}",
        [E48S, F60S, {"id": "DPW", "params": {"mult": m}}],
    )
# E: evidence-insurance floor
for a in (80, 150, 250):
    add(
        f"V2E_INS_a{a}",
        "E_insurance",
        f"pair + staleness floor age={a}",
        [E48S, F60S, {"id": "INS", "params": {"age": a}}],
    )
# F: learned switching controller (fitted on even development episodes)
for z, m in [(0.0, 1.0), (0.5, 1.0), (1.0, 1.0), (0.0, 1.5), (0.5, 1.5), (1.0, 1.5)]:
    add(
        f"V2F_LSW_z{z}_m{m}",
        "F_learned",
        f"pair + LSW z={z} mult={m}",
        [E48S, F60S, {"id": "LSW", "params": {"z": z, "mult": m}}],
    )
add(
    "V2F_LSW_alone_z0.5",
    "F_learned",
    "EQ+cut + LSW z=0.5 mult=1 (no E48/F60)",
    [{"id": "LSW", "params": {"z": 0.5}}],
)
# G: pre-existing learned acquisition controller on the pair
add(
    "V2G_F59tree",
    "G_learned_acq",
    "pair + F59 tree (search60 module, trained on even episodes of the nine)",
    [E48S, F60S, {"id": "F59", "setting": 0}],
)
add(
    "V2G_F59logit",
    "G_learned_acq",
    "pair + F59 logistic",
    [E48S, F60S, {"id": "F59", "setting": 1}],
)


def specs():
    return [{"name": n, "modules": m} for n, _, _, m in C]


if __name__ == "__main__":
    json.dump(specs(), open(sc.OUT / "specs_v2.json", "w"), indent=1)
    od = sc.DOCS / "algo"
    od.mkdir(parents=True, exist_ok=True)
    with open(od / "V2_CANDIDATES.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "family", "description", "modules"])
        for n, fam, d, m in C:
            w.writerow([n, fam, d, json.dumps(m)])
    print(len(C), "candidates")
