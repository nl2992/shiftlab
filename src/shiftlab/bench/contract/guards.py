"""Leak guards for the common operational contract.

Policies run inside ``policy_context()``. Evaluator-side objects derive from ``Sealed`` and raise
``LeakError`` on any non-dunder attribute read while a policy is executing. Attempts are also
recorded in a per-run list, so a policy that catches the exception still fails the run.

Scope: these guards catch accidental or lazy leakage (a policy holding a reference to the truth
object, to a pending label, to a stream). They are not a sandbox against adversarial code (gc
introspection, ctypes, process memory); confirmation runs should additionally execute policies
in a separate process that never receives evaluator objects.
"""

from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager

_IN_POLICY: contextvars.ContextVar[bool] = contextvars.ContextVar("d2a_in_policy", default=False)
_LEAKS: contextvars.ContextVar[list[str] | None] = contextvars.ContextVar("d2a_leaks", default=None)


class LeakError(RuntimeError):
    """A policy touched evaluator-side information."""


class LabelNotReleased(LeakError):
    """A policy tried to read a label value before its release time."""


def in_policy() -> bool:
    return _IN_POLICY.get()


def record_leak(what: str) -> None:
    sink = _LEAKS.get()
    if sink is not None:
        sink.append(what)


@contextmanager
def policy_context() -> Iterator[list[str]]:
    """Mark the enclosed code as policy code; yields the list of recorded leak attempts."""
    sink: list[str] = []
    t1 = _IN_POLICY.set(True)
    t2 = _LEAKS.set(sink)
    try:
        yield sink
    finally:
        _LEAKS.reset(t2)
        _IN_POLICY.reset(t1)


class Sealed:
    """Base class for evaluator-side objects: unreadable from inside policy code."""

    def __getattribute__(self, name: str):
        dunder = name.startswith("__") and name.endswith("__") and name != "__dict__"
        if _IN_POLICY.get() and not dunder:
            what = f"{type(self).__name__}.{name}"
            record_leak(what)
            raise LeakError(f"policy read evaluator-side attribute {what}")
        return object.__getattribute__(self, name)
