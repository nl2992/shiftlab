"""Apply the frozen R1 rule (docs/rpoq_next/REAL_DATA_PROTOCOL.md) to outputs/rpoq_next/r1/runs.csv."""

import csv
import json
import sys
from pathlib import Path

import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else "outputs/rpoq_next/r1/runs.csv"
rows = list(csv.DictReader(open(path)))  # noqa: SIM115
rng = np.random.default_rng(23)


def cohort_means(frac, arm, bet, field="log_wealth"):
    acc = {}
    for r in rows:
        if float(r["budget_fraction"]) == frac and r["arm"] == arm and r["bet"] == bet:
            v = float(r[field]) if field == "log_wealth" else float(r[field] == "True")
            acc.setdefault(int(r["cohort"]), []).append(v)
    return {k: float(np.mean(v)) for k, v in acc.items()}


def best_bet(frac, arm):
    return max(("ctx", "common"), key=lambda b: np.mean(list(cohort_means(frac, arm, b).values())))


def ci(a):
    a = np.asarray(a, float)
    boot = a[rng.integers(0, len(a), (2000, len(a)))].mean(1)
    return a.mean(), np.quantile(boot, 0.025), np.quantile(boot, 0.975)


out = {}
for frac in (0.05, 0.20):
    best = {a: best_bet(frac, a) for a in ("uniform", "neyman", "growth", "random_conc")}
    m = {a: cohort_means(frac, a, best[a]) for a in best}
    cr = {a: np.mean(list(cohort_means(frac, a, best[a], "crossed").values())) for a in best}
    base = max(("uniform", "neyman", "random_conc"), key=lambda a: np.mean(list(m[a].values())))
    ids = sorted(m["growth"])
    delta = [m["growth"][k] - m[base][k] for k in ids]
    out[str(frac)] = {
        "best_bet": best,
        "best_baseline": base,
        "delta": ci(delta),
        "mean_lw": {a: float(np.mean(list(m[a].values()))) for a in m},
        "crossing": cr,
    }
    print(f"budget {frac:.0%}: best bets {best}; best baseline = {base}")
    for a, vals in m.items():
        print(f"   {a:12s} LW={np.mean(list(vals.values())):7.2f}  crossing={cr[a]:.2f}")
    print("   Delta growth - best baseline: %.2f [%.2f, %.2f]" % out[str(frac)]["delta"])
Path("outputs/rpoq_next/r1/summary.json").write_text(json.dumps(out, indent=2))
