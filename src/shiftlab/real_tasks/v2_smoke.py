"""v2 harness on the real tasks: stream adapter and a descriptive DEV-only smoke table.

Run: ``python -m shiftlab.real_tasks.v2_smoke [--out path.json]``. Only the guarded development
loaders are used (OPSD < 2020, Binance 2025); a holdout timestamp raises before any file is read.
Nothing here is calibration or confirmatory evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ..contract.baselines import GatedHTFixed, GatedHTPaced, UniformHT
from ..contract.baselines_v2 import AlarmThenSwitch, DelayedHT
from ..contract.harness_v2 import HarnessResultV2, run_monitor_v2
from ..contract.interface_v2 import MonitorV2
from . import RealTask
from .binance_momentum import build_binance_task, load_binance_bars
from .opsd_reserve import build_opsd_tasks, load_opsd_hourly
from .r2_dev_measurements import (
    BINANCE_PACER_SEED_ROUNDS,
    BINANCE_ROOT,
    DEV_MONTHS,
    OPSD_PATH,
    SMOKE_SEED_BASE,
)

SMOKE_SEEDS_V2 = 50


def run_task_v2(
    task: RealTask,
    monitor: MonitorV2,
    budget_fraction: float,
    uniforms: np.ndarray,
    *,
    query_cost: float | None = None,
    switch_cost: float | None = None,
    **kwargs,
) -> HarnessResultV2:
    """Run ``monitor`` on a ``RealTask`` with its declared label release rounds, missing labels,
    losses and (by default) the primary imposed query and switch costs."""
    out = task.evaluator_outcomes()
    events = list(task.public_events())
    return run_monitor_v2(
        monitor,
        task.task_spec(budget_fraction),
        events,
        np.where(out.observed, out.paired_cost, 0.0),
        uniforms,
        np.full(len(events), task.price_unit),
        out.release_round,
        observed=out.observed,
        loss_incumbent=out.loss_incumbent,
        loss_candidate=out.loss_candidate,
        query_cost=task.costs.primary_query_cost if query_cost is None else query_cost,
        switch_cost=task.costs.primary_switch_cost if switch_cost is None else switch_cost,
        **kwargs,
    )


def _arms(seed_task: RealTask, rate: float) -> dict:
    val_dis = seed_task.public.disagreement
    ones = np.ones(len(val_dis))

    def fixed():
        return GatedHTFixed(
            validation_disagreement=val_dis, validation_tariffs=ones, budget_rate=rate
        )

    def paced():
        return GatedHTPaced(
            validation_disagreement=val_dis, validation_tariffs=ones, budget_rate=rate
        )

    return {
        "GatedHTFixed": lambda: DelayedHT(fixed()),
        "GatedHTPaced": lambda: DelayedHT(paced()),
        "UniformHT": lambda: DelayedHT(UniformHT(rate)),
    }


def smoke_v2(task: RealTask, seed_task: RealTask, budget_fraction: float, label: str) -> list[dict]:
    rows = []
    for name, make in _arms(seed_task, budget_fraction).items():
        for switching in (False, True):
            acc: dict[str, list] = {
                k: []
                for k in (
                    "alarm",
                    "first",
                    "spend",
                    "pend_end_n",
                    "pend_end_spend",
                    "max_pending",
                    "fb",
                    "missing",
                    "queries",
                    "refused",
                    "switches",
                    "switch_t",
                    "net",
                    "net_inc",
                    "net_cand",
                    "loss_dep",
                    "early",
                )
            }
            for s in range(SMOKE_SEEDS_V2):
                coins = np.random.default_rng(SMOKE_SEED_BASE + s).random(len(task))
                base = make()
                monitor = AlarmThenSwitch(base) if switching else base
                res = run_task_v2(task, monitor, budget_fraction, coins)
                acc["alarm"].append(res.first_alarm is not None)
                if res.first_alarm is not None:
                    acc["first"].append(res.first_alarm)
                acc["spend"].append(res.total_spend)
                acc["pend_end_n"].append(res.pending_at_end)
                acc["pend_end_spend"].append(res.pending_spend_at_end)
                acc["max_pending"].append(res.max_pending)
                acc["fb"].append(res.n_feedback_delivered)
                acc["missing"].append(res.n_missing_delivered)
                acc["queries"].append(res.n_queries)
                acc["refused"].append(int(res.refused.sum()))
                acc["switches"].append(res.n_switches)
                if res.switch_times:
                    acc["switch_t"].append(res.switch_times[0])
                acc["net"].append(res.net_utility)
                inc, cand = res.loss_sum_always_incumbent, res.loss_sum_always_candidate
                qc = res.query_cost * res.n_queries
                acc["net_inc"].append(-inc - qc)  # same queries, never switch
                acc["net_cand"].append(-cand - qc - res.switch_cost)  # same queries, switch at 0
                acc["loss_dep"].append(res.deployed_loss_sum)
                acc["early"].append(res.stopped_early)
            mean = lambda v: float(np.mean(v)) if len(v) else None
            rows.append(
                {
                    "task": label,
                    "monitor": name,
                    "switcher": "alarm_then_switch" if switching else "none",
                    "n_seeds": SMOKE_SEEDS_V2,
                    "n_rounds": len(task),
                    "alarm_seeds": int(sum(acc["alarm"])),
                    "median_first_alarm": float(np.median(acc["first"])) if acc["first"] else None,
                    "mean_spend_incl_pending": mean(acc["spend"]),
                    "budget": task.task_spec(budget_fraction).label_budget,
                    "mean_pending_at_end": mean(acc["pend_end_n"]),
                    "mean_pending_spend_at_end": mean(acc["pend_end_spend"]),
                    "mean_max_pending": mean(acc["max_pending"]),
                    "mean_feedback_delivered": mean(acc["fb"]),
                    "mean_missing_delivered": mean(acc["missing"]),
                    "mean_queries": mean(acc["queries"]),
                    "mean_refused": mean(acc["refused"]),
                    "mean_switches": mean(acc["switches"]),
                    "median_first_switch_round": float(np.median(acc["switch_t"]))
                    if acc["switch_t"]
                    else None,
                    "mean_net_utility": mean(acc["net"]),
                    "mean_net_utility_same_queries_never_switch": mean(acc["net_inc"]),
                    "mean_net_utility_same_queries_candidate_from_round0": mean(acc["net_cand"]),
                    "stopped_early_seeds": int(sum(acc["early"])),
                }
            )
    return rows


def delay_summary(task: RealTask) -> dict:
    out = task.outcomes
    delay = out.delay_rounds()[out.released]
    return {
        "release_round_offsets": sorted({int(v) for v in delay}),
        "labels_never_released_in_stream": int((~out.released).sum()),
        "labels_missing": int((~out.observed).sum()),
        "disagreement_rounds_missing": int(((~out.observed) & task.public.disagreement).sum()),
        "price_unit": task.price_unit,
        "query_cost": task.costs.primary_query_cost,
        "switch_cost": task.costs.primary_switch_cost,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    tasks, _ = build_opsd_tasks(load_opsd_hourly(OPSD_PATH))
    opsd_val, opsd_dev = tasks["validation"], tasks["development"]
    bin_all = build_binance_task(load_binance_bars(BINANCE_ROOT, DEV_MONTHS))
    bin_seed = bin_all.slice(0, BINANCE_PACER_SEED_ROUNDS)
    bin_dev = bin_all.slice(BINANCE_PACER_SEED_ROUNDS, len(bin_all))
    report = {
        "opsd_dev": delay_summary(opsd_dev),
        "binance_dev": delay_summary(bin_dev),
        "rows": smoke_v2(opsd_dev, opsd_val, 0.10, "opsd_dev_B10pct")
        + smoke_v2(bin_dev, bin_seed, 0.05, "binance_dev_B5pct"),
    }
    text = json.dumps(report, indent=2, default=float)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
