"""Shared figure style for the F3 TMLR paper (house style of figures4papers, re-implemented).

Spines top/right off, frameless legends, blue = proposed (shield), red = baselines, neutral = reference,
Helvetica/Arial-like sans, vector PDF (TrueType fonts embedded), PNG at 300 dpi.
Data paths are resolved relative to the worktree root.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # worktree root
RES = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget"
OUT = ROOT / "outputs/paper3/riskbudget"
CONFIGS = ROOT / "configs/paper3"

PALETTE = {
    "blue_main": "#0F4D92", "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE", "green_2": "#AADCA9", "green_3": "#8BCF8B",
    "red_1": "#F6CFCB", "red_2": "#E9A6A1", "red_strong": "#B64342",
    "neutral": "#CFCECE", "grey": "#767676", "dark": "#272727",
    "highlight": "#FFD700", "teal": "#42949E", "violet": "#9A4D8E",
}

# arm -> (label, colour, marker): blues/teal/violet = shield arms, reds/oranges = comparators
ARM_STYLE = {
    "f3_pi1": ("full sampling", PALETTE["blue_main"], "o"),
    "f3v2d": ("paced", PALETTE["teal"], "s"),
    "v3": ("v3", PALETTE["violet"], "^"),
}

WIDTH = 6.5  # inches, TMLR text width


def apply_style(font_size: float = 8.5, axes_linewidth: float = 0.9) -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": font_size,
        "axes.titlesize": font_size + 0.5,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size - 0.5,
        "ytick.labelsize": font_size - 0.5,
        "legend.fontsize": font_size - 0.5,
        "axes.linewidth": axes_linewidth,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "xtick.major.width": axes_linewidth, "ytick.major.width": axes_linewidth,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "lines.linewidth": 1.5,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "mathtext.default": "regular",
        "figure.dpi": 100, "savefig.dpi": 300,
    })


def panel_label(ax, s: str, dx: float = -0.0, dy: float = 1.04) -> None:
    ax.text(dx, dy, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")


def save(fig, name: str, pad: float = 0.3) -> None:
    """Write fig_<name>.pdf (vector) and fig_<name>.png (300 dpi) next to this file."""
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"fig_{name}.{ext}", dpi=300, bbox_inches="tight", pad_inches=pad / 3)
    plt.close(fig)


def load_json(p):
    return json.loads(Path(p).read_text())
