"""Reproduce paired summaries for the registered P6 Beta(2,1) pilot."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
ARTIFACT_DIR = Path(__file__).resolve().parent
RUN = ROOT / "outputs/scoped_method/p6_beta2_bounded_development_20261107"
OUT = ARTIFACT_DIR / "RESULTS.md"
CANDIDATE = "P6_LRMD_BETA2"
PUBLISHED = [
    "PFA-SR:gated_adaptive_range",
    "rmm:gated_adaptive_range+RMM",
    "E_rb:gated_adaptive_range+front",
    "gated_adaptive_range+front",
]
ALL = [
    "P6_LRMD_U",
    *PUBLISHED,
    "CONTROL_never_switch",
    "xu_acquisition_only",
]
BOOTSTRAP_SEED = 2026110714
N_BOOTSTRAP = 10_000


def load_rows():
    content = gzip.decompress((ARTIFACT_DIR / "records.jsonl.gz").read_bytes()).decode()
    rows = [json.loads(x) for x in content.splitlines()]
    by_regime = {}
    for r in rows:
        by_regime.setdefault(r["regime"], {}).setdefault(r["policy"], {})[r["seed"]] = r
    return by_regime


def ci_mean(x: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    take = rng.integers(0, len(x), size=(N_BOOTSTRAP, len(x)))
    means = x[take].mean(axis=1)
    return tuple(np.quantile(means, [0.025, 0.975]))


def main():
    raw_bytes = gzip.decompress((ARTIFACT_DIR / "records.jsonl.gz").read_bytes())
    compressed = ARTIFACT_DIR / "records.jsonl.gz"
    manifest = ARTIFACT_DIR / "manifest.json"
    regimes = load_rows()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    lines = [
        "# P6 Beta(2,1) bounded development pilot results",
        "",
        "This is development evidence only. The candidate is a conventional weighted restart prior;",
        "the pilot does not establish novelty or authorize real-data confirmation.",
        "",
        f"- Episode blocks: {sum(len(next(iter(p.values()))) for p in regimes.values())}",
        f"- Raw policy records: {len(raw_bytes.splitlines())}",
        f"- Runner manifest Git revision: `{json.loads(manifest.read_text())['git']}`",
        f"- Raw records SHA-256: `{hashlib.sha256(raw_bytes).hexdigest()}`",
        f"- Compressed records SHA-256: `{hashlib.sha256(compressed.read_bytes()).hexdigest()}`",
        f"- Manifest SHA-256: `{hashlib.sha256(manifest.read_bytes()).hexdigest()}`",
        f"- Analysis script SHA-256: `{hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}`",
        f"- Paired bootstrap: {N_BOOTSTRAP:,} draws, seed `{BOOTSTRAP_SEED}`, percentile 95% intervals.",
        "",
        "Negative paired differences favor the candidate. Loss, label and switching expenditures are",
        "reported as separate averages; net cost is the simulator's all-in deployment cost.",
        "",
    ]
    for regime, policies in regimes.items():
        if CANDIDATE not in policies:
            raise ValueError(f"missing candidate in {regime}")
        lines += [
            f"## {regime}",
            "",
            "| Policy | Mean net | Loss | Labels | Switches | Promote % | First promotion time* |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        means = {}
        for name in [CANDIDATE, *ALL]:
            if name not in policies:
                continue
            rs = list(policies[name].values())
            means[name] = float(np.mean([r["net"] for r in rs]))
            promoted = [r["first_deploy"] for r in rs if r["first_deploy"] >= 0]
            timing = f"{np.mean(promoted):.1f}" if promoted else "NA"
            lines.append(
                f"| `{name}` | {means[name]:.3f} | "
                f"{np.mean([r['loss'] for r in rs]):.3f} | "
                f"{np.mean([r['labels'] for r in rs]):.2f} | "
                f"{np.mean([r['switches'] for r in rs]):.3f} | "
                f"{100 * len(promoted) / len(rs):.1f}% | {timing} |"
            )
        lines += [
            "",
            "| Paired comparator | Mean difference | 95% bootstrap CI |",
            "|---|---:|---:|",
        ]
        cand_by_seed = policies[CANDIDATE]
        contrasts = {}
        for name in ["P6_LRMD_U", *PUBLISHED, "CONTROL_never_switch", "xu_acquisition_only"]:
            if name not in policies:
                continue
            shared = sorted(set(cand_by_seed) & set(policies[name]))
            d = np.array([cand_by_seed[s]["net"] - policies[name][s]["net"] for s in shared])
            lo, hi = ci_mean(d, rng)
            contrasts[name] = (float(d.mean()), lo, hi)
            lines.append(f"| `{name}` | {d.mean():.3f} | [{lo:.3f}, {hi:.3f}] |")
        best_published = min(PUBLISHED, key=lambda p: means[p] if p in means else float("inf"))
        if regime == "S_late_1500@B100":
            difference, lo, hi = contrasts[best_published]
            lines += [
                "",
                f"Strongest applicable published comparator by observed mean: `{best_published}`.",
                (
                    f"Primary gate: {'PASS' if difference <= -5 and hi < 0 else 'FAIL'} "
                    f"(candidate minus comparator = {difference:.3f}, 95% CI [{lo:.3f}, {hi:.3f}]; "
                    "requires mean <= -5 and upper bound < 0)."
                ),
            ]
        if "null" in regime:
            false = np.array([r["ever_promote"] for r in cand_by_seed.values()], dtype=int)
            n, x = len(false), int(false.sum())
            z = 1.96
            den = 1 + z**2 / n
            center = (x / n + z**2 / (2 * n)) / den
            half = z * np.sqrt((x / n * (1 - x / n) + z**2 / (4 * n)) / n) / den
            lines += [
                "",
                (
                    f"Candidate false promotions: {false.sum()}/{len(false)} "
                    f"({false.mean():.3%}; Wilson 95% CI [{max(0, center - half):.3%}, "
                    f"{min(1, center + half):.3%}]); descriptive only, not a guarantee test."
                ),
            ]
        if regime == "S_late_1500@B100":
            lines.append(
                "*Mean event index among episodes that promoted; `NA` means no promotions."
            )
        lines.append("")
    OUT.write_text("\n".join(lines))
    print(OUT.read_text(), end="")


if __name__ == "__main__":
    main()
