"""Draft inference and freeze checks; does not create confirmation worlds.

These utilities operate on independent whole-world replications. Event rows from
one dependent world must never be substituted for independent replications.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta


def binomial_upper(errors, worlds, *, alpha=0.05, family_size=1):
    """Bonferroni-adjusted one-sided exact Clopper-Pearson upper endpoint."""
    if type(errors) is not int or type(worlds) is not int or not 0 <= errors <= worlds or worlds < 1:
        raise ValueError("valid independent-world error counts required")
    if type(family_size) is not int or family_size < 1 or not 0 < alpha < 1:
        raise ValueError("valid family size and alpha required")
    return 1.0 if errors == worlds else float(beta.ppf(
        1 - alpha / family_size, errors + 1, worlds - errors
    ))


def paired_world_interval(candidate, parent, *, alpha=0.05, replications=5000, seed=0):
    """Percentile bootstrap over paired independent worlds, not over event rows.

    Intended for preregistered descriptive intervals. It is not exact finite-sample
    coverage, simultaneous coverage, or valid inference after unrestricted selection.
    Positive differences mean candidate minus parent; direction depends on metric.
    """
    x, y = np.asarray(candidate, float), np.asarray(parent, float)
    if x.ndim != 1 or y.shape != x.shape or len(x) < 2:
        raise ValueError("at least two aligned independent-world values required")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("world metrics must be finite")
    if type(replications) is not int or replications < 100 or not 0 < alpha < 1:
        raise ValueError("invalid bootstrap configuration")
    difference = x - y
    rng = np.random.default_rng(seed)
    bootstrap = np.empty(replications)
    for start in range(0, replications, 256):
        count = min(256, replications - start)
        index = rng.integers(len(x), size=(count, len(x)))
        bootstrap[start:start + count] = difference[index].mean(axis=1)
    lower, upper = np.quantile(bootstrap, [alpha / 2, 1 - alpha / 2])
    return {"mean_difference": float(difference.mean()), "lower": float(lower), "upper": float(upper),
            "independent_worlds": len(x), "method": "paired_world_percentile_bootstrap"}


def content_hash(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def freeze(path, *, candidates, source_hash, generator_hash, seed_specification, protocol_hash):
    """Exclusive-create a content-addressed selection record before any outcomes.

    This is an accidental-mutation safeguard, not a cryptographic access-control
    system. Future runner enforcement and exposure accounting remain required.
    """
    if not 1 <= len(candidates) <= 3:
        raise ValueError("freeze one to three targeted fixes")
    if len({content_hash(c) for c in candidates}) != len(candidates):
        raise ValueError("duplicate candidates")
    if not all(isinstance(x, str) and len(x) == 64 for x in (source_hash, generator_hash, protocol_hash)):
        raise ValueError("exact SHA256 provenance is required")
    body = {
        "candidates": candidates, "source_hash": source_hash, "generator_hash": generator_hash,
        "seed_specification": seed_specification, "protocol_hash": protocol_hash,
        "status": "frozen_before_confirmation_outcomes",
    }
    payload = {"body": body, "body_sha256": content_hash(body)}
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)
    return payload["body_sha256"]


def require_freeze(path, *, expected_body_hash, source_hash, generator_hash, protocol_hash):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    body = payload["body"]
    if content_hash(body) != expected_body_hash or payload["body_sha256"] != expected_body_hash:
        raise ValueError("confirmation freeze content mismatch")
    for key, value in (
        ("source_hash", source_hash), ("generator_hash", generator_hash), ("protocol_hash", protocol_hash),
    ):
        if body[key] != value:
            raise ValueError(f"confirmation {key} changed after selection")
    return body
