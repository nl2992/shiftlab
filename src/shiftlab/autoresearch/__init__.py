"""Structured candidate grammar, registry, experiment ledger and Stage-A preflight (WP5).

See docs/d2a_rar/AUTORESEARCH_PROGRAM.md and docs/d2a_rar/CANDIDATE_REGISTRY.md.
"""

from .grammar import (
    BATCH_SIZE,
    GRAMMAR_VERSION,
    MAX_IDENTITIES,
    build_registry,
    dedup,
    make_identity,
    priority_score,
    select_batch,
    validate_identity,
)

__all__ = [
    "BATCH_SIZE",
    "GRAMMAR_VERSION",
    "MAX_IDENTITIES",
    "build_registry",
    "dedup",
    "make_identity",
    "priority_score",
    "select_batch",
    "validate_identity",
]
