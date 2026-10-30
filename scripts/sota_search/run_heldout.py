"""Single-shot held-out evaluation of the frozen finalists (configs/sota_search/frozen_finalists_v1.json)."""

import json
import time
from pathlib import Path

import pandas as pd

from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h
from shiftlab.sota_search.db import Registry

spec = json.loads(Path("configs/sota_search/frozen_finalists_v1.json").read_text())
n_seeds = spec["heldout"]["seeds"]
worlds = h.heldout_pool()
sims = [g.simulate(w, n_seeds, spec["heldout"]["seed_block"] + i) for i, w in enumerate(worlds)]
null_cal = g.simulate(g.World(kind="none"), 400, 9000)
reg = Registry("outputs/sota_search/registry_heldout_g1.sqlite")
arms = {}
for name, f in spec["finalists"].items():
    arms[name] = (f["detector"], f["params"])
    if "marginal_control" in f:
        arms["CTRL_" + name] = (f["marginal_control"]["detector"], f["marginal_control"]["params"])
for name, c in spec["comparators"].items():
    arms[name] = (c["detector"], c["params"])
rows, t0 = [], time.time()
for frac in spec["fracs"]:
    base = {"frac": frac, "delay": spec["delay"], "tol": spec["tol"]}
    for arm, (det, params) in arms.items():
        p = {**base, **params}
        if det in ("page_hinkley", "cusum"):
            p.pop("tol")
        thr = h.calibrate(det, p, null_cal)
        for i, w in enumerate(worlds):
            m, rt = h.evaluate(
                det, p, w, sims[i], thr, lseed=spec["heldout"]["label_seed_block"] + i
            )
            role = h.role(w)
            tr = g.truth(w)
            reg.record(
                "heldout_g1",
                parent_algorithm=det,
                candidate_algorithm=arm,
                modification_id=arm,
                hyperparameters={**p, "threshold": thr},
                generator_family="G1_heldout",
                shift_type=f"{w.kind}/{w.shape}",
                shift_magnitude=w.delta,
                predictive_degradation=float(tr["predictive"].max()),
                decision_harm=float(tr["harm"].max()),
                delay_model="fixed_5",
                label_budget=frac,
                random_seed=spec["heldout"]["seed_block"] + i,
                execution_status="ok",
                primary_metric=m["detect_prob"],
                secondary_metrics={**m, "role": role},
                runtime=rt,
                labels_used=m["mean_labels"],
            )
            rows.append(
                {
                    "frac": frac,
                    "arm": arm,
                    "world": f"{w.kind}/{w.shape}/{w.delta:g}",
                    "role": role,
                    **{
                        k: m[k]
                        for k in (
                            "detect_prob",
                            "false_alarm_prob",
                            "mean_delay",
                            "mean_harm_before_alarm",
                            "mean_labels",
                        )
                    },
                }
            )
    reg.flush()
    print(f"frac {frac} done ({time.time() - t0:.0f}s)", flush=True)
df = pd.DataFrame(rows)
df.to_csv("outputs/sota_search/heldout_g1_summary.csv", index=False)
pd.set_option("display.width", 220)
for frac in spec["fracs"]:
    d = df[df.frac == frac]
    harm, ben, nul = d[d.role == "harm"], d[d.role == "benign"], d[d.role == "null"]
    t = pd.DataFrame(
        {
            "power_harm": harm.groupby("arm").detect_prob.mean(),
            "fa_benign": ben.groupby("arm").false_alarm_prob.mean(),
            "fa_null": nul.groupby("arm").false_alarm_prob.mean(),
            "harm_before": harm.groupby("arm").mean_harm_before_alarm.mean(),
        }
    )
    print(
        f"\n== held-out, label rate {frac} (harm worlds: {harm.world.nunique()}, benign: {ben.world.nunique()}) =="
    )
    print(t.round(3).to_string())
    piv = harm.pivot(index="world", columns="arm", values="detect_prob")
    print("per-world harm power:")
    print(piv.round(3).to_string())
