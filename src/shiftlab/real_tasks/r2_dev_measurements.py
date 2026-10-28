"""R2 development-window measurements and contract-harness smoke (descriptive, DEV only).

Run: ``python -m shiftlab.real_tasks.r2_dev_measurements [--out path.json]``. Reads raw data from
the main checkout's ``data/`` directory; only OPSD < 2020 and Binance 2025 are ever loaded.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ..contract.baselines import GatedHTFixed, GatedHTPaced, UniformHT
from ..contract.harness import run_monitor
from . import RealTask, run_length_summary
from .binance_momentum import build_binance_task, load_binance_bars
from .opsd_reserve import build_opsd_tasks, load_opsd_hourly, opsd_informative

MAIN = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter")
OPSD_PATH = MAIN / "data/raw/opsd/2020-10-06/hourly.csv"
BINANCE_ROOT = MAIN / "data/raw/binance"
DEV_MONTHS = [f"2025-{m:02d}" for m in range(1, 13)]
SMOKE_SEEDS = 200
SMOKE_SEED_BASE = 20261028
BINANCE_PACER_SEED_ROUNDS = 720


def stream_stats(task: RealTask) -> dict:
    pub, out = task.public, task.outcomes
    flags = pub.disagreement
    z = out.paired_cost
    stats = {
        "n_rounds": len(task),
        "exclusions": task.exclusions,
        **run_length_summary(flags, pub.adjacent_to_previous),
        "mean_paired_loss_all_rounds": float(z.mean()),
        "n_agreement_rounds_with_nonzero_Z": int(((~flags) & (np.abs(z) > 1e-12)).sum()),
        "max_abs_Z_on_agreement_rounds": float(np.abs(z[~flags]).max()) if (~flags).any() else 0.0,
        "min_Z": float(z.min()),
        "max_Z": float(z.max()),
    }
    if flags.any():
        zd = z[flags]
        stats.update(
            {
                "mean_paired_loss_on_disagreement": float(zd.mean()),
                "sd_paired_loss_on_disagreement": float(zd.std(ddof=1)) if len(zd) > 1 else None,
                "share_disagreement_with_Z_positive": float((zd > 0).mean()),
                "share_disagreement_with_Z_negative": float((zd < 0).mean()),
                "mean_paired_loss_on_disagreement_first_half": float(zd[: len(zd) // 2].mean()),
                "mean_paired_loss_on_disagreement_second_half": float(zd[len(zd) // 2 :].mean()),
            }
        )
    return stats


def smoke(task: RealTask, seed_task: RealTask, budget_fraction: float, label: str) -> dict:
    """Run GatedHTFixed/GatedHTPaced/UniformHT through the harness over many coin seeds.

    ``seed_task`` supplies the validation disagreement vector that seeds the pacer (past data
    only). The contract harness has no label delay: feedback is delivered immediately (d=0).
    """
    events = list(task.public_events())
    spec = task.task_spec(budget_fraction)
    val_dis = seed_task.public.disagreement
    ones_val = np.ones(len(val_dis))
    prices = np.full(len(events), task.price_unit)
    rate = budget_fraction
    factories = {
        "GatedHTFixed": lambda: GatedHTFixed(
            validation_disagreement=val_dis, validation_tariffs=ones_val, budget_rate=rate
        ),
        "GatedHTPaced": lambda: GatedHTPaced(
            validation_disagreement=val_dis, validation_tariffs=ones_val, budget_rate=rate
        ),
        "UniformHT": lambda: UniformHT(rate),
    }
    result = {}
    for name, make in factories.items():
        alarms, first, spend, agree_q, dis_q, early, maxlog = [], [], [], [], [], [], []
        for s in range(SMOKE_SEEDS):
            coins = np.random.default_rng(SMOKE_SEED_BASE + s).random(len(events))
            res = run_monitor(make(), spec, events, task.outcomes.paired_cost, coins, prices)
            alarms.append(res.first_alarm is not None)
            if res.first_alarm is not None:
                first.append(res.first_alarm)
            spend.append(res.total_spend)
            flags = task.public.disagreement[: res.processed]
            dis_q.append(int((res.queried & flags).sum()))
            agree_q.append(int((res.queried & ~flags).sum()))
            early.append(res.stopped_early)
            maxlog.append(float(res.log_e.max()))
        result[name] = {
            "label": label,
            "alarm_count_of_seeds": int(sum(alarms)),
            "n_seeds": SMOKE_SEEDS,
            "median_first_alarm_round": float(np.median(first)) if first else None,
            "mean_label_spend": float(np.mean(spend)),
            "budget": spec.label_budget,
            "mean_labels_on_disagreement": float(np.mean(dis_q)),
            "mean_labels_on_agreement": float(np.mean(agree_q)),
            "stopped_early_count": int(sum(early)),
            "mean_max_log_e": float(np.mean(maxlog)),
            "log_threshold": float(-np.log(spec.alpha)),
        }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    series = load_opsd_hourly(OPSD_PATH)
    tasks, model = build_opsd_tasks(series)
    opsd_val, opsd_dev = tasks["validation"], tasks["development"]
    bars = load_binance_bars(BINANCE_ROOT, DEV_MONTHS)
    bin_all = build_binance_task(bars)
    seed_n = BINANCE_PACER_SEED_ROUNDS
    bin_seed, bin_dev = bin_all.slice(0, seed_n), bin_all.slice(seed_n, len(bin_all))
    report = {
        "opsd": {
            "ridge_penalty": model.penalty,
            "validation_mse_by_penalty": model.validation_mse,
            "n_train_days_hour0": model.n_train,
            "validation_exclusions": opsd_val.exclusions,
            "development": stream_stats(opsd_dev),
            "informative_2_to_60_percent": opsd_informative(
                float(opsd_dev.public.disagreement.mean())
            ),
            "release_round_offsets_used": sorted(
                {int(v) for v in (opsd_dev.outcomes.release_round - np.arange(len(opsd_dev)))}
            ),
            "smoke_B10pct": smoke(opsd_dev, opsd_val, 0.10, "opsd_dev"),
        },
        "binance": {
            "development_all_rounds": stream_stats(bin_all),
            "pacer_seed_rounds": seed_n,
            "monitor_stream": stream_stats(bin_dev),
            "release_round_offsets_used": sorted(
                {int(v) for v in (bin_all.outcomes.release_round - np.arange(len(bin_all)))}
            ),
            "smoke_B5pct": smoke(bin_dev, bin_seed, 0.05, "binance_dev"),
        },
    }
    text = json.dumps(report, indent=2, default=float)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
