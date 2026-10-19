"""Composable, configured synthetic scenarios."""

from .generators import SCENARIOS, generate_chunks
from .presets import conformal_stress_catalogue, decision_stress_catalogue

__all__ = [
    "SCENARIOS",
    "conformal_stress_catalogue",
    "decision_stress_catalogue",
    "generate_chunks",
]
