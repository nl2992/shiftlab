"""Shared figure style for the Paper 4 TMLR draft.

Follows the figures4papers conventions (github.com/ChenLiu-1996/figures4papers,
scientific-figure-making/references/api.md): its PALETTE, blue = proposed method (RB-DP),
red = baselines, neutral = reference, top/right spines off, frameless legends, sans-serif,
vector PDF with embedded TrueType fonts and PNG at 300 dpi. Re-implemented here; no code copied.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # worktree root
RBDP = ROOT / "docs/paper4_continuation/rbdp"
REAL = RBDP / "real_data/results"

PALETTE = {
    "blue_main": "#0F4D92", "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE", "green_2": "#AADCA9", "green_3": "#8BCF8B",
    "red_1": "#F6CFCB", "red_2": "#E9A6A1", "red_strong": "#B64342",
    "neutral": "#CFCECE", "grey": "#767676", "dark": "#272727",
    "highlight": "#FFD700", "teal": "#42949E", "violet": "#9A4D8E",
}

WIDTH = 6.5  # inches, TMLR text width


def apply_style(font_size: float = 8.5, axes_linewidth: float = 1.25) -> None:
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
        "xtick.major.size": 4, "ytick.major.size": 4,
        "lines.linewidth": 1.8,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "mathtext.default": "regular",
        "figure.dpi": 100, "savefig.dpi": 300,
    })


def panel_label(ax, s: str, dx: float = -0.12, dy: float = 1.04) -> None:
    ax.text(dx, dy, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")


def save(fig, name: str, pad: float = 0.3) -> None:
    """Write fig_<name>.pdf (vector) and fig_<name>.png (300 dpi) next to this file."""
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"fig_{name}.{ext}", dpi=300, bbox_inches="tight", pad_inches=pad / 3)
    plt.close(fig)


def read_jsonl(p):
    return [json.loads(line) for line in Path(p).read_text().splitlines() if line.strip()]


# darker shades used for schematic titles (title colour = darker shade of the glyph fill)
PASTEL = {"pink": "#F6CFCB", "blue": "#CFE3F6", "grey": "#E3E2E2", "lav": "#E6DAEE", "butter": "#FCEFC7",
          "sage": "#DDE5C8"}
DARK = {"blue": "#1B3A6B", "lav": "#4B2A6B", "red": "#8B1E1E", "sage": "#3E5A2A"}
