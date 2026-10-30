"""Q1 baseline grid on the development pool; every (config, world) is recorded in the registry."""

import csv
import itertools
import json
import sys
import time
from pathlib import Path

from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h
from shiftlab.sota_search.db import Registry

FRACS, DELAYS = (0.05, 0.10, 0.20), (0, 5, 20)


def configs():
    for w in (50, 100, 200):
        for name in ("mmd", "c2st", "bbsd"):
            yield name, {"win": w}
    for f, d in itertools.product(FRACS, DELAYS):
        for s in (0.25, 0.5, 1.0):
            yield "cusum", {"frac": f, "delay": d, "slack": s}
        for dl in (0.05, 0.1, 0.25):
            yield "page_hinkley", {"frac": f, "delay": d, "delta": dl}
        for w in (30, 60, 120):
            yield "twowin", {"frac": f, "delay": d, "w": w}
        for tol in (0.0, 0.05):
            for name in ("pr_cs", "pprm", "pp_cost"):
                yield name, {"frac": f, "delay": d, "tol": tol}
        yield "watch", {"frac": f, "delay": d}


def main(n_seeds=200, limit_s=1800):
    t_start = time.time()
    reg = Registry("outputs/sota_search/registry.sqlite")
    worlds = h.dev_pool()
    sims = {w.key() + str(i): g.simulate(w, n_seeds, 1000 + i) for i, w in enumerate(worlds)}
    keys = list(sims)
    null_sim = g.simulate(g.World(kind="none"), 400, 9000)
    rows = []
    for ci, (name, params) in enumerate(configs()):
        if time.time() - t_start > limit_s:
            print("time limit reached; stopping cleanly", flush=True)
            break
        try:
            cal_sim = (
                null_sim
                if name not in ("mmd", "c2st", "bbsd")
                else g.simulate(g.World(kind="none"), 200, 9001)
            )
            thr = h.calibrate(name, params, cal_sim)
        except Exception as e:  # noqa: BLE001
            reg.record(
                "q1_baselines",
                candidate_algorithm=name,
                parent_algorithm=name,
                hyperparameters=params,
                execution_status="implementation_defect",
                failure_reason=repr(e),
            )
            continue
        for i, (w, k) in enumerate(zip(worlds, keys, strict=True)):
            try:
                m, rt = h.evaluate(name, params, w, sims[k], thr, lseed=500 + i)
                status = "ok"
            except Exception as e:  # noqa: BLE001
                reg.record(
                    "q1_baselines",
                    candidate_algorithm=name,
                    parent_algorithm=name,
                    hyperparameters=params,
                    generator_family="G1",
                    shift_type=w.key(),
                    execution_status="implementation_defect",
                    failure_reason=repr(e),
                )
                continue
            tr = g.truth(w)
            role = h.role(w)
            reg.record(
                "q1_baselines",
                parent_algorithm=name,
                candidate_algorithm=name,
                modification_id="none",
                component_configuration=name,
                hyperparameters={**params, "threshold": thr},
                generator_family="G1",
                shift_type=f"{w.kind}/{w.shape}",
                shift_magnitude=w.delta,
                predictive_degradation=float(tr["predictive"].max()),
                decision_harm=float(tr["harm"].max()),
                proxy_quality="calibrated_model",
                delay_model=f"fixed_{params.get('delay', 0)}",
                label_budget=params.get("frac"),
                cost_configuration={"fn": g.FN_COST, "fp": g.FP_COST},
                random_seed=1000 + i,
                baseline_version="SOURCE_INSPIRED_OR_LOCAL",
                execution_status=status,
                validity_status="empirical_threshold"
                if name not in h.det.THEORY_THRESHOLD
                else "theory_threshold",
                primary_metric=m["detect_prob"],
                secondary_metrics={**m, "role": role},
                runtime=rt,
                labels_used=m["mean_labels"],
            )
            rows.append(
                {
                    "detector": name,
                    "params": json.dumps(params, sort_keys=True),
                    "world": w.key(),
                    "role": role,
                    **{
                        k2: m[k2]
                        for k2 in (
                            "detect_prob",
                            "false_alarm_prob",
                            "mean_delay",
                            "mean_harm_before_alarm",
                            "mean_labels",
                        )
                    },
                    "threshold": thr,
                    "runtime": rt,
                }
            )
        reg.flush()
        if ci % 20 == 0:
            print(f"config {ci} {name} {params} ({time.time() - t_start:.0f}s)", flush=True)
    out = Path("outputs/sota_search/q1_baselines_summary.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("runs recorded:", reg.count(), "seconds", round(time.time() - t_start), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
