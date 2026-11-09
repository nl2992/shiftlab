#!/usr/bin/env python3
"""Generate reproducible 1-5-module candidate manifests for Paper 1.

THIS DOES NOT RUN THE SHIFT Lab EXPERIMENTS. It proposes manifests that an agent
can implement and execute using scripts/paper1_eqsdp/stage2_eval.py and the
existing nine-dataset seal. The full 25-policy comparator panel is not modified.

Examples:
    python paper1_combo_sampler.py bootstrap --out paper1_initial_candidates.jsonl
    python paper1_combo_sampler.py guided --results results.csv --out paper1_guided_candidates.jsonl

The guided mode uses Bayesian ridge regression with additive 60-module effects,
21 family-pair effects and 5 cardinality effects. This is only a cheap proposal
model; it does not establish Bayesian novelty or simulated superiority.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from itertools import combinations_with_replacement
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "paper1_60_contraptions.json"
SEED = 20261109
SIZES = {1: 60, 2: 200, 3: 160, 4: 120, 5: 80}
# Alternative posterior state engines must not silently overwrite one another.
EXCLUSIVE_GROUPS = [{"C21", "C24", "C25", "C26", "C29", "C30"}]


def load_catalog():
    d = json.loads(CATALOG.read_text())
    entries = d["modules"]
    assert len(entries) == 60, "Expect exactly 60 catalogued modules"
    return d, {r["id"]: r for r in entries}


def valid(combo):
    return 1 <= len(combo) <= 5 and all(len(set(combo) & g) <= 1 for g in EXCLUSIVE_GROUPS)


def cid(combo):
    c = sorted(combo)
    return f"K{len(c)}__" + "_".join(c)


def spec(combo, catalog, phase):
    c = sorted(combo)
    return {
        "combo_id": cid(c),
        "modules": c,
        "cardinality": len(c),
        "families": sorted({catalog[k]["family"] for k in c}),
        "phase": phase,
        "parent": "s2armr_H1100",
        "status": "NOT_RUN",
    }


def generate_random(ids, k, count, seen, rng, prefer_cross_family=True):
    out = []
    attempts = 0
    while len(out) < count and attempts < 500000:
        attempts += 1
        combo = tuple(sorted(rng.choice(ids, k, replace=False).tolist()))
        if not valid(combo) or combo in seen:
            continue
        if (
            prefer_cross_family
            and k > 1
            and len({x[0] for x in combo}) < min(k, 3)
            and rng.random() < 0.8
        ):
            continue
        seen.add(combo)
        out.append(combo)
    if len(out) < count:
        raise RuntimeError(f"Only {len(out)}/{count} unique size-{k} candidates available")
    return out


def bootstrap(catalog, rng):
    ids = sorted(catalog)
    combos = [(k,) for k in ids]
    seen = set(combos)
    for k in range(2, 6):
        combos.extend(generate_random(ids, k, SIZES[k], seen, rng))
    return combos


def make_features(combo, ids, family_pairs):
    loc = {id: i for i, id in enumerate(ids)}
    x = np.zeros(1 + len(ids) + len(family_pairs) + 5)
    x[0] = 1.0
    for k in combo:
        x[1 + loc[k]] = 1.0
    fs = [k[0] for k in combo]
    cs = Counter(fs)
    off = 1 + len(ids)
    for i, p in enumerate(family_pairs):
        if p[0] == p[1]:
            x[off + i] = cs[p[0]] * (cs[p[0]] - 1) / 2
        else:
            x[off + i] = cs[p[0]] * cs[p[1]]
    x[-5 + len(combo) - 1] = 1.0
    return x


def posterior(rows, ids, pairs, target="delta_j"):
    # Bayesian linear regression with regularizing N(0, sigma_prior^2) coefficients.
    # Do NOT use this posterior for scientific inference, only proposal ranking.
    D = 1 + len(ids) + len(pairs) + 5
    precision = np.eye(D) / 16.0
    precision[0, 0] = 1 / 100.0
    rhs = np.zeros(D)
    used = 0
    for row in rows:
        try:
            parts = row["combo_id"].split("__", 1)[1].split("_")
            y = float(row[target])
            se = float(row.get("se_j", "0.75") or 0.75)
            if not math.isfinite(y) or not math.isfinite(se):
                continue
            if any(k not in ids for k in parts) or not valid(parts):
                continue
            x = make_features(parts, ids, pairs)
            weight = 1 / max(se, 0.2) ** 2
            precision += np.outer(x, x) * weight
            rhs += x * y * weight
            used += 1
        except (KeyError, ValueError, IndexError):
            continue
    cov = np.linalg.inv(precision)
    mean = cov @ rhs
    return mean, cov, used


def guided(catalog, rng, results, num=240):
    ids = sorted(catalog)
    fs = "ABCDEF"
    family_pairs = list(combinations_with_replacement(fs, 2))
    with Path(results).open(newline="") as f:
        rows = list(csv.DictReader(f))
    mean, cov, used = posterior(rows, ids, family_pairs)
    loss_mean, loss_cov, loss_used = posterior(rows, ids, family_pairs, target="delta_loss_pp")
    if used < 10:
        raise ValueError(
            "Guided search requires >=10 valid evaluated rows with combo_id,delta_j,se_j"
        )
    previously = {
        tuple(sorted(x["combo_id"].split("__")[1].split("_")))
        for x in rows
        if "combo_id" in x and "__" in x["combo_id"]
    }
    # Sample possible 1..5 combinations; the sampler is cheap and not a simulator.
    seen = set(previously)
    proposals = []
    for size, count in ((2, 1000), (3, 8000), (4, 8000), (5, 8000)):
        proposals += generate_random(ids, size, count, set(seen), rng)
    # Add singletons that were never evaluated.
    proposals += [(x,) for x in ids if (x,) not in previously]
    proposals = [c for c in sorted(set(proposals)) if c not in seen]
    # Thompson selection: sample regression coefficients and penalize high module count.
    beta = rng.multivariate_normal(mean, cov)
    beta_loss = rng.multivariate_normal(loss_mean, loss_cov) if loss_used >= 10 else None
    feats = np.stack([make_features(c, ids, family_pairs) for c in proposals])
    predicted_dJ = feats @ beta
    predicted_dL = feats @ beta_loss if beta_loss is not None else np.zeros(len(feats))
    score = (
        -predicted_dJ
        - 5.0 * np.maximum(0, predicted_dL - 0.1)
        - 0.04 * (np.array([len(c) for c in proposals]) - 1)
    )
    ranks = np.argsort(-score)
    output = []
    chosen = set()
    quota = {1: 20, 2: 75, 3: 65, 4: 50, 5: 30}
    for idx in ranks:
        c = proposals[idx]
        if len(output) >= num:
            break
        if quota[len(c)] <= 0:
            continue
        if c in chosen:
            continue
        chosen.add(c)
        output.append(c)
        quota[len(c)] -= 1
    return output, used


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=["bootstrap", "guided"])
    p.add_argument("--results", help="CSV with combo_id,delta_j,se_j; needed for guided phase")
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args()
    _, catalog = load_catalog()
    rng = np.random.default_rng(args.seed)
    if args.phase == "bootstrap":
        combos = bootstrap(catalog, rng)
        used = 0
    else:
        if not args.results:
            p.error("--results is required for guided")
        combos, used = guided(catalog, rng, args.results)
    assert len({cid(c) for c in combos}) == len(combos)
    with Path(args.out).open("w") as f:
        f.writelines(json.dumps(spec(c, catalog, args.phase)) + "\n" for c in combos)
    print(
        json.dumps(
            {
                "phase": args.phase,
                "proposals": len(combos),
                "size_histogram": dict(Counter(map(len, combos))),
                "results_used": used,
                "out": args.out,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
