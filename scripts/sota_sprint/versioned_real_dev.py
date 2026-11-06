"""Exploratory chronological real-data version update screen; does not touch registered caches."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for p in (
    ROOT / "scripts/failure_atlas_v2_flq",
    ROOT / "scripts/promising_directions/sota",
    ROOT / "scripts/promising_directions/sota/competitors",
    HERE,
):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import fresh_real
from bench import CONTRACT
from registry import EXTRA
from simulator import run_episode
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from suite import build_suite
from versioned_challenger import (
    VersionAwareModelPicker,
    VersionIndexedGate,
    VersionIndexedRollbackGate,
)

T = 2000
UPDATE = 1000
TRAIN2 = 100
POLICIES = [
    "rmm:gated_adaptive_range+RMM",
    "gated_adaptive_range+front",
    "A5b",
    "CONTROL_never_switch",
]


def fit_predict(name):
    x, raw_y, ts = fresh_real.LOADERS[name]()
    cat = fresh_real.CATEGORICAL.get(name, [])
    for c in cat:
        x[c] = x[c].astype(str)
    n = len(x)
    n30 = int(0.30 * n)
    y = (raw_y.to_numpy() > float(np.median(raw_y.to_numpy()[:n30]))).astype(np.int8)
    # All compared policies receive identical prediction paths. Version 2 is trained strictly
    # before activation, using a separately accounted training-label purchase at the boundary.
    f0 = fresh_real.prep(x.iloc[: int(0.15 * n)], cat)
    m0 = LogisticRegression(max_iter=300, C=1.0).fit(
        f0(x.iloc[: int(0.15 * n)]), y[: int(0.15 * n)]
    )
    f1 = fresh_real.prep(x.iloc[:n30], cat)
    m1 = HistGradientBoostingClassifier(
        max_iter=100, max_depth=4, learning_rate=0.1, random_state=0
    )
    m1.fit(f1(x.iloc[:n30]), y[:n30])
    # v2's new supervised labels come only from a separate, explicitly purchased 100-row block
    # between the two scored windows. Previously this code accidentally trained on every label
    # through train2_end while charging only 100 labels.
    train2_start = n30 + UPDATE
    train2_end = train2_start + TRAIN2
    if train2_end + UPDATE > n:
        raise ValueError(f"{name}: insufficient rows after charged v2 training block")
    known_train_rows = np.r_[np.arange(n30), np.arange(train2_start, train2_end)]
    f2 = fresh_real.prep(x.iloc[known_train_rows], cat)
    m2 = HistGradientBoostingClassifier(
        max_iter=100, max_depth=4, learning_rate=0.1, random_state=1
    )
    m2.fit(f2(x.iloc[known_train_rows]), y[known_train_rows])
    xx1 = f1(x.iloc[n30 : n30 + UPDATE])
    xx2 = f2(x.iloc[train2_end : train2_end + UPDATE])
    pred_v1 = np.column_stack((m0.predict(f0(x.iloc[n30 : n30 + UPDATE])), m1.predict(xx1))).astype(
        np.int8
    )
    pred_v2 = np.column_stack(
        (m0.predict(f0(x.iloc[train2_end : train2_end + UPDATE])), m2.predict(xx2))
    ).astype(np.int8)
    pred_v1_all = np.column_stack((pred_v1[:, 0], pred_v1[:, 1], pred_v1[:, 1]))
    # Model slots are immutable: 0=incumbent, 1=v1, 2=v2. During v2's window,
    # v1 remains a valid deployed baseline and must retain its own predictions.
    pred_v2_v1 = m1.predict(f1(x.iloc[train2_end : train2_end + UPDATE])).astype(np.int8)
    pred_v2_all = np.column_stack((pred_v2[:, 0], pred_v2_v1, pred_v2[:, 1]))
    pred = np.vstack((pred_v1_all, pred_v2_all)).astype(np.int8)
    labels = np.r_[y[n30 : n30 + UPDATE], y[train2_end : train2_end + UPDATE]]
    contexts = np.r_[np.ones(UPDATE, dtype=np.int8), np.full(UPDATE, 2, dtype=np.int8)]
    # The reported errors refer only to the two scored windows, not to the intervening
    # v2-training block.
    err = [float(np.mean(pred_v1[:, i] != y[n30 : n30 + UPDATE])) for i in (0, 1)]
    err += [float(np.mean(pred_v2[:, i] != y[train2_end : train2_end + UPDATE])) for i in (0, 1)]
    return (
        pred,
        labels,
        contexts,
        {
            "n_rows": n,
            "train_v1_end": n30,
            "train_v2_start": train2_start,
            "train_v2_end": train2_end,
            "v2_new_label_rows": [train2_start, train2_end],
            "v2_sunk_training_rows": int(n30),
            "timestamp_start": str(ts.iloc[n30]),
            "timestamp_update": str(ts.iloc[train2_end]),
            "timestamp_end": str(ts.iloc[train2_end + UPDATE - 1]),
            "training_labels_for_v2": TRAIN2,
            "training_label_cost": float(TRAIN2 * CONTRACT["cq"]),
            "errors": err,
            "late_window_errors": [
                float(np.mean(pred_v2_all[:, i] != y[train2_end : train2_end + UPDATE]))
                for i in range(3)
            ],
        },
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", default=",".join(fresh_real.LOADERS))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for di, name in enumerate(args.datasets.split(",")):
        pred, y, ctx, meta = fit_predict(name)
        # The v2 fitting block is part of the claimed policy cost and shared label cap.
        remaining_budget = max(0, CONTRACT["budget"] - meta["training_labels_for_v2"])
        delay = fresh_real.DELAYS[name]
        policies = build_suite(
            UPDATE,
            remaining_budget,
            CONTRACT["cs"],
            CONTRACT["cq"],
            CONTRACT["alpha"],
            delay,
            di,
            2026110911,
            names=POLICIES,
            extra=EXTRA,
        )
        # Two-model baselines see the currently available version in a replaceable challenger slot.
        pair = pred[:, [0, 1]].copy()
        pair[UPDATE:, 1] = pred[UPDATE:, 2]
        for policy in policies:
            res = run_episode(
                policy,
                model_predictions=pair,
                labels=y,
                contexts=ctx,
                delay=delay,
                budget=remaining_budget,
                label_price=CONTRACT["cq"],
                switch_cost=CONTRACT["cs"],
                trace=True,
            )
            rows.append(
                {
                    "dataset": name,
                    "policy": policy.name,
                    "net": res.net_cost + meta["training_label_cost"],
                    "loss": res.prediction_loss,
                    "labels": res.requested_labels + meta["training_labels_for_v2"],
                    "policy_labels": res.requested_labels,
                    "training_labels": meta["training_labels_for_v2"],
                    "switches": res.deployment_switches,
                    "ever_promote": int(any(r["deployed_model"] == 1 for r in res.records)),
                    **meta,
                }
            )
        gate = VersionIndexedGate(2, remaining_budget, CONTRACT["alpha"])
        res = run_episode(
            gate,
            model_predictions=pred,
            labels=y,
            contexts=ctx,
            delay=delay,
            budget=remaining_budget,
            label_price=CONTRACT["cq"],
            switch_cost=CONTRACT["cs"],
            trace=True,
        )
        rows.append(
            {
                "dataset": name,
                "policy": gate.name,
                "net": res.net_cost + meta["training_label_cost"],
                "loss": res.prediction_loss,
                "labels": res.requested_labels + meta["training_labels_for_v2"],
                "policy_labels": res.requested_labels,
                "training_labels": meta["training_labels_for_v2"],
                "switches": res.deployment_switches,
                "ever_promote": int(bool(gate.promotions)),
                "promotions": gate.promotions,
                "labels_by_version": gate.labels_by_version,
                **meta,
            }
        )
        rollback_gate = VersionIndexedRollbackGate(2, remaining_budget, CONTRACT["alpha"])
        rr = run_episode(
            rollback_gate,
            model_predictions=pred,
            labels=y,
            contexts=ctx,
            delay=delay,
            budget=remaining_budget,
            label_price=CONTRACT["cq"],
            switch_cost=CONTRACT["cs"],
            trace=True,
        )
        rows.append(
            {
                "dataset": name,
                "policy": rollback_gate.name,
                "net": rr.net_cost + meta["training_label_cost"],
                "loss": rr.prediction_loss,
                "labels": rr.requested_labels + meta["training_labels_for_v2"],
                "policy_labels": rr.requested_labels,
                "training_labels": meta["training_labels_for_v2"],
                "switches": rr.deployment_switches,
                "ever_promote": int(bool(rollback_gate.promotions)),
                "promotions": rollback_gate.promotions,
                "rollbacks": rollback_gate.rollbacks,
                "labels_by_version": rollback_gate.labels_by_version,
                **meta,
            }
        )
        # Post-hoc allocation sensitivity: reserve 25% of alpha/budget for v1 and 75% for v2.
        # This is exploratory reuse of the same five streams, not independent validation.
        weighted = VersionIndexedGate(
            2, remaining_budget, CONTRACT["alpha"], version_weights=(1.0, 3.0)
        )
        res = run_episode(
            weighted,
            model_predictions=pred,
            labels=y,
            contexts=ctx,
            delay=delay,
            budget=remaining_budget,
            label_price=CONTRACT["cq"],
            switch_cost=CONTRACT["cs"],
            trace=True,
        )
        rows.append(
            {
                "dataset": name,
                "policy": "version_indexed_gate_v1v2_1to3",
                "net": res.net_cost + meta["training_label_cost"],
                "loss": res.prediction_loss,
                "labels": res.requested_labels + meta["training_labels_for_v2"],
                "policy_labels": res.requested_labels,
                "training_labels": meta["training_labels_for_v2"],
                "switches": res.deployment_switches,
                "ever_promote": int(bool(weighted.promotions)),
                "promotions": weighted.promotions,
                "labels_by_version": weighted.labels_by_version,
                "alpha_by_version": weighted.alpha_by_version.tolist(),
                "budget_by_version": weighted.budget_by_version.tolist(),
                **meta,
            }
        )
        mp = VersionAwareModelPicker(2, np.random.default_rng(2026110911 + di))
        res = run_episode(
            mp,
            model_predictions=pred,
            labels=y,
            contexts=ctx,
            delay=delay,
            budget=remaining_budget,
            label_price=CONTRACT["cq"],
            switch_cost=CONTRACT["cs"],
            trace=True,
        )
        rows.append(
            {
                "dataset": name,
                "policy": mp.name,
                "net": res.net_cost + meta["training_label_cost"],
                "loss": res.prediction_loss,
                "labels": res.requested_labels + meta["training_labels_for_v2"],
                "policy_labels": res.requested_labels,
                "training_labels": meta["training_labels_for_v2"],
                "switches": res.deployment_switches,
                "ever_promote": int(any(r["deployed_model"] > 0 for r in res.records)),
                **meta,
            }
        )
        print(
            name,
            [
                (r["policy"], round(r["net"], 2), r["labels"], r["ever_promote"])
                for r in rows
                if r["dataset"] == name
            ],
            flush=True,
        )
    (out / "records.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
