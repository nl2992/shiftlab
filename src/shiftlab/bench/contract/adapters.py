"""Adapter interfaces for COMMON_CONTRACT_PORT of native controllers (stubs).

Drift2Act (src/shiftlab/sota/drift2act/) and RAR (src/shiftlab/sota/rar/) are written by other
agents. A port implements ``NativeAdapter`` and yields a ``BasePolicy``-compatible object; it must
(i) consume only ``ObservableState``, (ii) declare its action vocabulary subset, (iii) report which
null (cond / marg / abs_risk) its gate claims (key into registry/null_assumptions.yaml), and
(iv) never import evaluator-side classes (``streams.EvaluatorTruth`` / ``Stream``).

Proposed action maps (the owning agent confirms):
  Drift2Act  low-cost action -> switch(CANDIDATE) or continue; escalation -> retrain;
             rollback scheduling -> rollback; fallback/handoff -> abstain; audit sample -> query;
             certificate-failure notice -> alert.  B_lab = BudgetSpec.label_cap.
  RAR        serving -> continue; canary stages -> switch(CANDIDATE) (the contract keeps a single
             model in force, so canary traffic splitting is a documented loss of fidelity; native
             Suite A keeps the staged canary); retrain gate -> retrain; rollback -> rollback;
             Alert-Hold-Soft -> alert; Alert-Hold-Hard -> alert + abstain.  The label-fraction gate
             counts ``state.H``, never truth.
"""

from __future__ import annotations

from typing import Protocol

from .policies import BasePolicy
from .types import ACTION_KINDS, EnvSpec


class NativeAdapter(Protocol):
    name: str
    vocabulary: tuple[str, ...]  # subset of ACTION_KINDS
    claimed_null: str  # 'cond' | 'marg' | 'abs_risk' | 'none'
    port_status: str  # 'COMMON_CONTRACT_PORT' once ported

    def build(self, env: EnvSpec) -> BasePolicy: ...


class _StubAdapter:
    vocabulary = ACTION_KINDS
    claimed_null = "none"
    port_status = "STUB_NOT_PORTED"

    def __init__(self, name: str) -> None:
        self.name = name

    def build(self, env: EnvSpec) -> BasePolicy:
        raise NotImplementedError(f"{self.name}: COMMON_CONTRACT_PORT pending (WP1a/WP1b agents)")


# Ported adapters (WP1a/WP1b, 2026-11-07); the stub class is kept for future hosts.
from .adapters_drift2act import Drift2ActAdapter
from .adapters_rar import BinaryAdapter, CostAwareBinaryAdapter, RARAdapter

__all__ = [
    "BinaryAdapter",
    "CostAwareBinaryAdapter",
    "Drift2ActAdapter",
    "NativeAdapter",
    "RARAdapter",
]
