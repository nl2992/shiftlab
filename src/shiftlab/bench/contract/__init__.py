"""Common operational contract (Suite B) for the Drift2Act/RAR programme.

See docs/d2a_rar/BENCHMARK_CONTRACT.md.
"""
# ruff: noqa: F401

from .audit import AUDIT_SCHEMA_VERSION, AuditLog, AuditViolation, verify_run
from .costs import load_cost_vectors
from .guards import LabelNotReleased, LeakError, Sealed, policy_context
from .paired import PairedRuns, UnpairedError, assert_paired, paired_bootstrap_ci, run_paired
from .policies import AlwaysContinue, BasePolicy, UniformQueryNaiveSwitch
from .simulator import Ledger, RunResult, Simulator
from .streams import (
    ConfirmationAccessError,
    DelaySpec,
    EvaluatorTruth,
    MissingSpec,
    Stream,
    StreamSpec,
    list_families,
    load_family,
    make_stream,
)
from .types import (
    Action,
    ActionNotAllowed,
    BudgetExceeded,
    BudgetSpec,
    ClockSpec,
    CostVector,
    EnvSpec,
    ObservableState,
    ReleasedLabel,
)
