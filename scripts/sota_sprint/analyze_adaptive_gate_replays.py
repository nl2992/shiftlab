#!/usr/bin/env python3
"""Paired audit of original outputs against MOPE interval correction replays."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

TAG = "_mopeinterval_20261106"
KEYS = ["kind", "regime", "ep", "seed", "policy"]


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, float(mid - half)), min(1.0, float(mid + half))


def paired_ci(values: pd.Series) -> tuple[float, float, float]:
    v = values.astype(float).to_numpy()
    if len(v) < 2:
        return float(np.mean(v)) if len(v) else float("nan"), float("nan"), float("nan")
    mean = float(np.mean(v))
    half = float(stats.t.ppf(0.975, len(v) - 1) * stats.sem(v))
    return mean, mean - half, mean + half


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("outputs"))
    parser.add_argument("--json", type=Path, default=Path("outputs/sprint2/mope_interval_replay_differences.json"))
    parser.add_argument("--csv", type=Path, default=Path("outputs/sprint2/mope_interval_replay_differences.csv"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/sprint2/mope_interval_replay_differences.md"))
    args = parser.parse_args()

    results = []
    coverage = []
    missing_sources = []
    for manifest_path in sorted(args.root.rglob("manifest.json")):
        new_dir = manifest_path.parent
        if TAG not in new_dir.name:
            continue
        old_name = new_dir.name.replace(TAG, "")
        if "_retry" in old_name:
            old_name = old_name.split("_retry", 1)[0]
        old_dir = new_dir.with_name(old_name)
        old_path, new_path = old_dir / "records.jsonl", new_dir / "records.jsonl"
        if not new_path.is_file():
            continue
        if not old_path.is_file():
            missing_sources.append({"corrected_run": str(new_dir), "expected_source_run": str(old_dir),
                                    "corrected_rows": sum(1 for _ in new_path.open()),
                                    "reason": "original records.jsonl is unavailable"})
            continue
        old = pd.read_json(old_path, lines=True)
        new = pd.read_json(new_path, lines=True)
        old = old[old.policy.isin(set(new.policy))].copy()
        if not set(KEYS).issubset(old) or not set(KEYS).issubset(new):
            raise ValueError(f"missing paired key columns in {old_dir} or {new_dir}")
        if old.duplicated(KEYS).any() or new.duplicated(KEYS).any():
            raise ValueError(f"duplicate pairing keys in {old_dir} or {new_dir}")
        cmp = old.merge(new, on=KEYS, suffixes=("_old", "_new"), validate="one_to_one", how="outer", indicator=True)
        old_only = int((cmp["_merge"] == "left_only").sum())
        new_only = int((cmp["_merge"] == "right_only").sum())
        is_reconstructed_h_partial = str(old_dir).endswith("outputs/sprint2/H/screen1")
        if (old_only or new_only) and not is_reconstructed_h_partial:
            missing = cmp.loc[cmp["_merge"] != "both", KEYS + ["_merge"]].head(10).to_dict("records")
            raise ValueError(f"old/new replay keys do not match for {new_dir}: {missing}")
        coverage.append({"source_run": str(old_dir), "corrected_run": str(new_dir),
                         "old_rows_for_replayed_policies": len(old), "corrected_rows": len(new),
                         "matched_rows": int((cmp["_merge"] == "both").sum()),
                         "old_only_rows": old_only, "corrected_only_rows": new_only,
                         "partial_reconstruction": bool(is_reconstructed_h_partial)})
        cmp = cmp.loc[cmp["_merge"] == "both"].drop(columns="_merge")
        if cmp.empty:
            continue
        for field in ("alpha", "budget", "delay", "cs", "cq"):
            if f"{field}_old" in cmp and f"{field}_new" in cmp:
                if not np.allclose(cmp[f"{field}_old"], cmp[f"{field}_new"], equal_nan=True):
                    raise ValueError(f"contract mismatch in {field} between old and corrected rows for {new_dir}")
        cmp["delta_net"] = cmp.net_new - cmp.net_old
        cmp["delta_labels"] = cmp.labels_new - cmp.labels_old
        cmp["delta_switches"] = cmp.switches_new - cmp.switches_old
        cmp["promotion_changed"] = cmp.ever_promote_old != cmp.ever_promote_new
        for (regime, policy), g in cmp.groupby(["regime", "policy"], sort=True):
            k_old = int(g.ever_promote_old.sum())
            k_new = int(g.ever_promote_new.sum())
            lo_old, hi_old = wilson(k_old, len(g))
            lo_new, hi_new = wilson(k_new, len(g))
            dm, dlo, dhi = paired_ci(g.delta_net)
            results.append({
                "source_run": str(old_dir), "corrected_run": str(new_dir),
                "manifest_sha256": digest(manifest_path), "regime": regime, "policy": policy,
                "n": len(g), "promotions_old": k_old, "rate_old": k_old / len(g),
                "wilson_old_lo": lo_old, "wilson_old_hi": hi_old,
                "promotions_corrected": k_new, "rate_corrected": k_new / len(g),
                "wilson_corrected_lo": lo_new, "wilson_corrected_hi": hi_new,
                "delta_promotions": k_new - k_old,
                "promotion_changed_n": int(g.promotion_changed.sum()),
                "delta_net_mean": dm, "delta_net_ci_lo": dlo, "delta_net_ci_hi": dhi,
                "delta_labels_mean": float(g.delta_labels.mean()),
                "delta_switches_mean": float(g.delta_switches.mean()),
            })

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    results = [{k: (None if isinstance(v, (float, np.floating)) and not np.isfinite(v) else v)
                for k, v in row.items()} for row in results]
    frame = pd.DataFrame(results)
    frame.to_csv(args.csv, index=False)
    payload = {"purpose": "same-seed, same-stream code-correction sensitivity; not independent confirmation",
               "cells": results, "cell_count": len(results), "coverage": coverage,
               "missing_sources": missing_sources,
               "corrected_runs": sorted({r["corrected_run"] for r in results})}
    args.json.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    lines = [
        "# MOPE interval correction replay differences", "",
        "Matched old versus corrected output rows use the same stream, episode, seed and policy. These are correction replays after a discovered implementation defect; they are not independent validation or new confirmatory data.", "",
        f"- Corrected run directories with matched output: **{len(payload['corrected_runs'])}**",
        f"- Matched regime-policy cells: **{len(results)}**",
        "- Paired row coverage is listed below; the reconstructed H partial run is compared only on confirmed common keys.",
        f"- Machine-readable row-level table: `outputs/sprint2/adaptive_gate_replay_differences.csv`",
        f"- JSON with source manifest SHA256 values: `outputs/sprint2/adaptive_gate_replay_differences.json`", "",
        "| Source run | Regime | Policy | n | Promote old → corrected | Changed | Δ net [95% paired CI] | Δ labels | Δ switches |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    def fmt(x: float | None) -> str:
        return "n/a" if x is None else f"{x:+.2f}"

    for r in results:
        lines.append(f"| `{r['source_run']}` | {r['regime']} | {r['policy']} | {r['n']} | "
                     f"{r['promotions_old']}/{r['n']} → {r['promotions_corrected']}/{r['n']} | "
                     f"{r['promotion_changed_n']} | {fmt(r['delta_net_mean'])} [{fmt(r['delta_net_ci_lo'])},{fmt(r['delta_net_ci_hi'])}] | "
                     f"{r['delta_labels_mean']:+.2f} | {r['delta_switches_mean']:+.2f} |")
    lines += ["", "## Paired-row coverage", "",
              "| Source run | Old rows for replayed policies | Corrected rows | Matched | Old only | Corrected only | Partial reconstruction |",
              "|---|---:|---:|---:|---:|---:|---|"]
    for r in coverage:
        lines.append(f"| `{r['source_run']}` | {r['old_rows_for_replayed_policies']} | {r['corrected_rows']} | "
                     f"{r['matched_rows']} | {r['old_only_rows']} | {r['corrected_only_rows']} | "
                     f"{'yes' if r['partial_reconstruction'] else 'no'} |")
    if missing_sources:
        lines += ["", "## Corrected outputs without original records", "",
                  "These outputs exist, but the superseded source records are unavailable, so no paired correction difference is claimed.",
                  "", "| Corrected run | Expected source run | Corrected rows | Reason |", "|---|---|---:|---|"]
        for r in missing_sources:
            lines.append(f"| `{r['corrected_run']}` | `{r['expected_source_run']}` | {r['corrected_rows']} | {r['reason']} |")
    args.markdown.write_text("\n".join(lines) + "\n")
    print(f"matched corrected run dirs={len(payload['corrected_runs'])} cells={len(results)}")


if __name__ == "__main__":
    main()
