"""Frozen cost vectors (configs/d2a_rar/cost_vectors.yaml) with checksum verification."""

from __future__ import annotations

from pathlib import Path

from .types import CostVector, cost_vector_fingerprint


def load_cost_vectors(path: Path | None = None) -> dict[str, CostVector]:
    import yaml

    p = path or Path(__file__).resolve().parents[4] / "configs" / "d2a_rar" / "cost_vectors.yaml"
    doc = yaml.safe_load(p.read_text(encoding="utf8"))
    vecs = doc["vectors"]
    if cost_vector_fingerprint(vecs) != doc["content_sha256"]:
        raise ValueError("cost_vectors.yaml was modified after freezing (checksum mismatch)")
    return {k: CostVector(name=k, **v) for k, v in vecs.items()}
