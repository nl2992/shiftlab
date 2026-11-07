"""Analyze every row from the frozen, paired synthetic screen."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

HERE = Path(__file__).resolve().parent
CELLS = ("F1_late_800", "F0_better", "F3_reversal_800", "F0_null")
METHODS = (
    "P7s_MP_overlay",
    "P7s_MP_no_settled_throttle",
    "P7s_settled",
    "model_picker_adapter",
    "D1",
    "gated_adaptive_range+front",
    "CONTROL_never_switch",
)


def mean_ci(values):
    x = np.asarray(values, dtype=float)
    mean = float(x.mean())
    half = float(student_t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)))
    return mean, mean - half, mean + half


def main():
    rows = [json.loads(s) for s in (HERE / "raw_episode_rows.jsonl").read_text().splitlines()]
    expected = len(CELLS) * 50 * len(METHODS)
    if len(rows) != expected:
        raise ValueError(f"expected {expected} episode rows, found {len(rows)}")
    by = {(r["cell"], r["policy"], r["seed"]): r for r in rows}
    for c in CELLS:
        for m in METHODS:
            if sorted(by[(c, m, s)]["seed"] for s in range(50)) != list(range(50)):
                raise ValueError(f"incomplete pairing for {c}/{m}")

    lines = [
        "# Frozen overlay pilot results",
        "",
        "All 50 seeds in each registered cell and all seven methods are included. Paired 95% t intervals use the shared synthetic seeds. This is a development screen, not confirmation.",
        "",
        "## Per-method outcomes",
        "",
        "| Cell | Method | Net cost (95% CI) | Loss | Label cost | Switch cost | Labels | Switches | Promotions | Rollbacks | Median promotion t |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for c in CELLS:
        for m in METHODS:
            rs = [by[(c, m, s)] for s in range(50)]
            mu, lo, hi = mean_ci([r["net_cost"] for r in rs])
            pts = [r["first_promotion_t"] for r in rs if r["first_promotion_t"] >= 0]
            lines.append(
                f"| {c} | {m} | {mu:.2f} [{lo:.2f}, {hi:.2f}] | "
                f"{np.mean([r['predictive_loss'] for r in rs]):.2f} | "
                f"{np.mean([r['label_expenditure'] for r in rs]):.2f} | "
                f"{np.mean([r['switch_expenditure'] for r in rs]):.2f} | "
                f"{np.mean([r['labels'] for r in rs]):.1f} | "
                f"{np.mean([r['switches'] for r in rs]):.2f} | "
                f"{sum(r['promotion_count'] for r in rs)} | "
                f"{sum(r['rollback_count'] for r in rs)} | "
                f"{np.median(pts) if pts else 'NA'} |"
            )
    lines += ["", "## Frozen development rule", ""]
    passed = True
    for comparator in ("model_picker_adapter", "P7s_settled"):
        d = [
            by[("F1_late_800", "P7s_MP_overlay", s)]["net_cost"]
            - by[("F1_late_800", comparator, s)]["net_cost"]
            for s in range(50)
        ]
        mu, lo, hi = mean_ci(d)
        ok = mu <= -5 and hi < 0
        passed &= ok
        lines.append(
            f"- F1_late_800 candidate minus {comparator}: {mu:.2f} [{lo:.2f}, {hi:.2f}]; requires mean <= -5 and upper CI < 0: **{'PASS' if ok else 'FAIL'}**."
        )
    for c in ("F3_reversal_800", "F0_null"):
        d = [
            by[(c, "P7s_MP_overlay", s)]["net_cost"]
            - by[(c, "CONTROL_never_switch", s)]["net_cost"]
            for s in range(50)
        ]
        mu, lo, hi = mean_ci(d)
        ok = mu <= 5
        passed &= ok
        lines.append(
            f"- {c} excess versus never-switch: {mu:.2f} [{lo:.2f}, {hi:.2f}]; requires mean <= 5: **{'PASS' if ok else 'FAIL'}**."
        )
    null_promos = sum(by[("F0_null", "P7s_MP_overlay", s)]["promotion_count"] for s in range(50))
    ok = null_promos <= 5
    passed &= ok
    lines.append(
        f"- F0_null candidate promotions: {null_promos}/50; requires <=5/50: **{'PASS' if ok else 'FAIL'}**."
    )
    lines += [
        "",
        f"**Development gate: {'PASS' if passed else 'FAIL'}.** A pass permits only separate prior-art review and frozen independent evaluation.",
        "",
        "## Audit notes",
        "",
        "The runner aborts on a refused request, a budget exceedance, or any mismatch between the combined issue propensity and CertPlus's frozen propensity. The compressed event trace records every synthetic event and every method; the manifest contains source and output hashes.",
        "",
    ]
    out = HERE / "RESULTS.md"
    out.write_text("\n".join(lines))
    manifest_path = HERE / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["analysis_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest["results_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("\n".join(lines[-10:]))


if __name__ == "__main__":
    main()
