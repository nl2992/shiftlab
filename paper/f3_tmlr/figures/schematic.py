"""Helpers for illustrated concept / process figures in the figures4papers style (see STYLE_SPEC.md).

Drawn in inch coordinates on a figure-sized axes. Objects are flat, thin-outlined and softly filled; gradients are
done with clipped imshow; keywords in callouts are bold and coloured, as in the reference composites.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

from style import PALETTE as P

MONO = ["Courier New", "Menlo", "DejaVu Sans Mono"]
OUTLINE = "#3A3A3A"
BLUE_LIGHT = "#CFE0F3"
RED_LIGHT = "#F6D5D2"
GREEN_LIGHT = "#DFF1DF"
CALLOUT = {  # fill, edge, keyword colour
    "green": ("#E8F4E6", "#B9DDB6", "#3F7F3B"),
    "red": ("#F9E3E0", P["red_strong"], P["red_strong"]),
    "blue": ("#E6EEF8", "#9DB9DE", P["blue_main"]),
    "gold": ("#FBF1D6", "#E7CF8E", "#A57B0B"),
}


def canvas(W: float, H: float):
    fig = plt.figure(figsize=(W, H), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    ax._W, ax._H = W, H
    return fig, ax


def finish(ax):
    """imshow resets limits and aspect; restore the inch frame."""
    ax.set_xlim(0, ax._W)
    ax.set_ylim(0, ax._H)
    ax.set_aspect("auto")


def inset(fig, W, H, x, y, w, h):
    return fig.add_axes([x / W, y / H, w / W, h / H])


# ----------------------------------------------------------------------------- fills
def gradient_patch(ax, patch, c0, c1, vertical=True, zorder=2):
    """Fill an existing patch with a linear gradient c0 -> c1 (bottom to top, or left to right)."""
    ax.add_patch(patch)
    x0, y0, x1, y1 = patch.get_path().get_extents().transformed(patch.get_patch_transform()).extents
    g = np.linspace(0, 1, 96)
    g = g.reshape(-1, 1) if vertical else g.reshape(1, -1)
    im = ax.imshow(g, extent=(x0, x1, y0, y1), origin="lower", aspect="auto",
                   cmap=LinearSegmentedColormap.from_list("g", [c0, c1]), zorder=zorder)
    im.set_clip_path(patch)
    return im


def cell(ax, x, y, w, h, fill, ec=OUTLINE, lw=0.7, r=0.035, grad=None, zorder=3, ls="-", hatch=None):
    """A token-like rounded cell, optionally with a vertical gradient (c0, c1)."""
    patch = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                           fc="none" if grad else fill, ec=ec, lw=lw, zorder=zorder + 0.2, ls=ls, hatch=hatch)
    if grad:
        gradient_patch(ax, patch, grad[0], grad[1], vertical=True, zorder=zorder)
        patch.set_zorder(zorder + 0.2)
    else:
        ax.add_patch(patch)
    return patch


def panel(ax, x, y, w, h, fill="white", ec=OUTLINE, lw=0.9, r=0.09, ls="-", zorder=1, shadow=False):
    if shadow:
        for k, a in ((0.035, 0.05), (0.022, 0.07), (0.01, 0.09)):
            ax.add_patch(FancyBboxPatch((x + k * 0.6, y - k), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc="black",
                                        ec="none", alpha=a, zorder=zorder - 0.05))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fill, ec=ec, lw=lw, ls=ls,
                                zorder=zorder))


def frame(ax, x, y, w, h, color=None, lw=1.5, r=0.09, zorder=7):
    """Rounded highlight frame (the red frame around the key object)."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc="none",
                                ec=color or P["red_strong"], lw=lw, zorder=zorder))


def zoom_cone(ax, src, dst, color=None, alpha=0.2, zorder=1.5):
    """Translucent cone from a small rectangle src=(x0,y0,x1,y1) to a larger one dst, as in the sphere zoom."""
    (a0, b0, a1, b1), (c0, d0, c1, d1) = src, dst
    if b0 >= d1:  # dst below src
        pts = [(a0, b0), (a1, b0), (c1, d1), (c0, d1)]
    else:
        pts = [(a0, b1), (a1, b1), (c1, d0), (c0, d0)]
    ax.add_patch(Polygon(pts, closed=True, fc=color or P["blue_secondary"], ec="none", alpha=alpha, zorder=zorder))


def block_arrow(ax, x, y, w, h, c0=BLUE_LIGHT, c1=P["blue_secondary"], head=0.34, zorder=2):
    """Wide flat arrow with a left-to-right gradient, carrying the takeaway sentence."""
    b = h * 0.62
    yc = y + h / 2
    pts = [(x, yc - b / 2), (x + w - head, yc - b / 2), (x + w - head, y), (x + w, yc), (x + w - head, y + h),
           (x + w - head, yc + b / 2), (x, yc + b / 2)]
    gradient_patch(ax, Polygon(pts, closed=True, fc="none", ec="none"), c0, c1, vertical=False, zorder=zorder)


def arrow(ax, p, q, color=None, lw=1.2, rad=0.0, ms=7, ls="-", zorder=4, style="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, lw=lw, color=color or OUTLINE, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0, zorder=zorder))


# ----------------------------------------------------------------------------- text
def _w(ax, s, fs, **kw):
    r = ax.figure.canvas.get_renderer()
    a = ax.text(0, 0, "|" + s + "|", fontsize=fs, **kw)
    b = ax.text(0, 0, "||", fontsize=fs, **kw)
    w = (a.get_window_extent(r).width - b.get_window_extent(r).width) / ax.figure.dpi
    a.remove()
    b.remove()
    return w


def rich(ax, x, y, parts, fs=7, ha="left", va="center", zorder=8, color=None):
    """One line made of styled parts: [(text, {weight, color, style, family}), ...]; bold coloured keywords.
    Spaces at the edges of a part become an explicit gap (matplotlib does not measure edge spaces reliably)."""
    gap = 0.29 * fs / 72.0
    items = []  # (text, kw, lead_gap, width)
    prev_trail = False
    for t, kw in parts:
        lead, trail = t.startswith(" "), t.endswith(" ")
        core = t.strip()
        items.append((core, kw, gap if (lead or prev_trail) and items else 0.0, _w(ax, core, fs, **kw)))
        prev_trail = trail
    total = sum(w + g for _, _, g, w in items)
    x0 = x - total / 2 if ha == "center" else (x - total if ha == "right" else x)
    for core, kw, g, w in items:
        x0 += g
        k = dict(kw)
        k.setdefault("color", color or P["dark"])
        ax.text(x0, y, core, fontsize=fs, ha="left", va=va, zorder=zorder, **k)
        x0 += w
    return total


def callout(ax, x, y, w, h, lines, tint="green", fs=6.6, r=0.07, lw=0.9, ls="-", lead=0.155):
    """Pale rounded callout; `lines` is a list of lines, each a list of (text, is_keyword) pairs."""
    fill, edge, kc = CALLOUT[tint]
    panel(ax, x, y, w, h, fill=fill, ec=edge, lw=lw, r=r, ls=ls, zorder=2)
    n = len(lines)
    y0 = y + h / 2 + (n - 1) * lead / 2
    for i, line in enumerate(lines):
        parts = [(t, dict(weight="bold", color=kc) if kw else dict(color=P["dark"])) for t, kw in line]
        rich(ax, x + w / 2, y0 - i * lead, parts, fs=fs, ha="center")


def mono(ax, x, y, s, fs=6.6, ha="left", va="center", color=None, weight="normal", **kw):
    ax.text(x, y, s, fontsize=fs, ha=ha, va=va, family=MONO, color=color or P["dark"], fontweight=weight, zorder=8, **kw)


def tag(ax, x, y, s, fs=10):
    ax.text(x, y, s, fontsize=fs, fontweight="bold", ha="left", va="center", zorder=9)


def banner(ax, x, y, w, h, parts, fs=7.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.08", fc="white", ec=OUTLINE, lw=0.9,
                                ls=(0, (4, 2.2)), zorder=2))
    rich(ax, x + w / 2, y + h / 2, parts, fs=fs, ha="center")


# ----------------------------------------------------------------------------- flat icons
def icon_shield(ax, cx, cy, s=0.2, color=None, zorder=9):
    c = color or P["blue_main"]
    pts = [(cx - s * .5, cy + s * .5), (cx, cy + s * .62), (cx + s * .5, cy + s * .5), (cx + s * .5, cy - s * .02),
           (cx + s * .3, cy - s * .35), (cx, cy - s * .6), (cx - s * .3, cy - s * .35), (cx - s * .5, cy - s * .02)]
    ax.add_patch(Polygon(pts, closed=True, fc=c, ec=OUTLINE, lw=0.7, zorder=zorder, joinstyle="round"))
    ax.plot([cx - s * .22, cx - s * .04, cx + s * .26], [cy - s * .02, cy - s * .2, cy + s * .2], color="white", lw=1.2,
            zorder=zorder + 0.1, solid_capstyle="round")


def icon_clock(ax, cx, cy, r=0.08, zorder=9):
    ax.add_patch(Circle((cx, cy), r, fc="white", ec=OUTLINE, lw=0.8, zorder=zorder))
    ax.plot([cx, cx], [cy, cy + r * .65], color=OUTLINE, lw=0.8, zorder=zorder + .1)
    ax.plot([cx, cx + r * .5], [cy, cy - r * .1], color=OUTLINE, lw=0.8, zorder=zorder + .1)


def icon_coin(ax, cx, cy, r=0.075, label="k", zorder=9):
    ax.add_patch(Circle((cx, cy), r, fc="#F3C94F", ec="#A57B0B", lw=0.8, zorder=zorder))
    ax.text(cx, cy - 0.003, label, fontsize=6, ha="center", va="center", fontweight="bold", color="#6B4E00",
            zorder=zorder + .1, style="italic")


def macros(*files):
    out = {}
    for f in files:
        for m in re.finditer(r"\\newcommand\{\\(\w+)\}\{(.*)\}", Path(f).read_text()):
            out[m.group(1)] = m.group(2).replace("{,}", ",").replace("$-$", "-")
    return out


# ----------------------------------------------------------------------------- raster assets and speech cards
def load_icon(path, white_thresh=0.93, soft=0.07):
    """Load a PNG drawn on white and return an RGBA array: near-white becomes transparent (soft edge), cropped to content."""
    from PIL import Image
    im = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255.0
    lum = im.min(axis=2)
    alpha = np.clip((white_thresh - lum) / soft, 0, 1)
    rgba = np.dstack([im, alpha])
    ys, xs = np.where(alpha > 0.05)
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def cut_sheet(path, rows=2, cols=2):
    """Split an icon sheet into rows x cols auto-cropped RGBA icons (row-major)."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    W_, H_ = im.size
    out = []
    for r in range(rows):
        for c in range(cols):
            tile = im.crop((c * W_ // cols, r * H_ // rows, (c + 1) * W_ // cols, (r + 1) * H_ // rows))
            tmp = Path(path).with_name(f"_tile_{r}{c}.png")
            tile.save(tmp)
            out.append(load_icon(tmp))
            tmp.unlink()
    return out


def paste(ax, rgba, cx, cy, height, zorder=6):
    """Place an RGBA icon centred at (cx, cy) with the given height in inches."""
    h, w = rgba.shape[:2]
    wd = height * w / h
    ax.imshow(rgba, extent=(cx - wd / 2, cx + wd / 2, cy - height / 2, cy + height / 2), zorder=zorder, aspect="auto")
    return wd


def bubble(ax, x, y, w, h, tail=None, fill="white", ec=OUTLINE, lw=0.9, r=0.07, zorder=2):
    """Rounded speech card with an optional pointed tail towards `tail`=(tx, ty), as the question/answer cards in VIGIL."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fill, ec=ec, lw=lw, zorder=zorder))
    if tail:
        tx, ty = tail
        cx = min(max(tx, x + r * 2), x + w - r * 2)
        if ty < y:  # tail below
            pts = [(cx - 0.05, y + 0.003), (cx + 0.05, y + 0.003), (tx, ty)]
        elif ty > y + h:
            pts = [(cx - 0.05, y + h - 0.003), (cx + 0.05, y + h - 0.003), (tx, ty)]
        elif tx < x:
            pts = [(x + 0.003, y + h / 2 - 0.05), (x + 0.003, y + h / 2 + 0.05), (tx, ty)]
        else:
            pts = [(x + w - 0.003, y + h / 2 - 0.05), (x + w - 0.003, y + h / 2 + 0.05), (tx, ty)]
        ax.add_patch(Polygon(pts, closed=True, fc=fill, ec=ec, lw=lw, zorder=zorder + 0.1, joinstyle="round"))
        ax.add_patch(Polygon(pts[:2] and [pts[0], pts[1], pts[1], pts[0]], closed=True, fc=fill, ec="none", zorder=zorder + 0.2))
