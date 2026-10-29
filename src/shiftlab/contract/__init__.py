"""Public monitor contract: the only surface an external method may import.

This package re-exports ``interface`` only. The evaluator side (``harness``) and the in-repo
baselines (``baselines``) must be imported explicitly and are not available to external adapters.
"""

from .interface import Feedback, Monitor, PublicEvent, TaskSpec

__all__ = ["Feedback", "Monitor", "PublicEvent", "TaskSpec"]
