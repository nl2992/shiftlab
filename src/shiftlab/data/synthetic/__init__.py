"""Composable, configured synthetic scenarios."""

from .generators import SCENARIOS, generate_chunks
from .oracle_spec import conditional_mean, conditional_scale, oracle_spec
from .presets import conformal_stress_catalogue, decision_stress_catalogue

__all__ = [
    "SCENARIOS",
    "conditional_mean",
    "conditional_scale",
    "conformal_stress_catalogue",
    "decision_stress_catalogue",
    "generate_chunks",
    "oracle_spec",
]
