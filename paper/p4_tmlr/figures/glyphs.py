"""Small drawing helpers for the schematics (figures4papers style): shaded spheres, gradient block arrows,
monospace token strips, trapezoid 'models', segmented state bars. All coordinates are inches (axes aspect is equal)."""
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.patches import Polygon, Rectangle, FancyArrowPatch

MONO = {"family": ["Courier New", "Courier", "DejaVu Sans Mono"], "weight": "bold"}


def sphere(ax, c, r, color, z=3):
    """Lit sphere as in figure_Dispersion/plot_idea.py (normals from x,y,z; light from top left), tinted."""
    n = 256
    xs = np.linspace(-1, 1, n); x, y = np.meshgrid(xs, xs)
    r2 = x ** 2 + y ** 2; m = r2 <= 1
    zz = np.sqrt(np.clip(1 - r2, 0, None))
    L = np.array([-0.5, 0.5, 0.8]); L /= np.linalg.norm(L)
    inten = np.clip(x * L[0] + y * L[1] + zz * L[2], 0, 1)
    shade = np.clip(0.55 + 0.6 * inten, 0, 1.15)
    base = np.array(to_rgb(color))
    rgb = np.clip(base[None, None, :] * shade[..., None] + 0.25 * np.clip(inten - 0.8, 0, 1)[..., None] * 4 * (1 - base), 0, 1)
    img = np.dstack([rgb, m.astype(float)])
    ax.imshow(img, origin="lower", extent=(c[0] - r, c[0] + r, c[1] - r, c[1] + r), zorder=z, interpolation="bilinear")
    from matplotlib.patches import Circle
    ax.add_patch(Circle(c, r, fc="none", ec="#272727", lw=1.1, zorder=z + 1))


def block_arrow(ax, x0, x1, y, h, color, z=2, vertical=False):
    """Chunky block arrow with a light-to-tint gradient (stream colour)."""
    L = abs(x1 - x0); hd = min(L * 0.55, h * 0.62); sh = h * 0.5 / 2
    if not vertical:
        pts = [(x0, y - sh), (x1 - hd, y - sh), (x1 - hd, y - h / 2), (x1, y), (x1 - hd, y + h / 2), (x1 - hd, y + sh), (x0, y + sh)]
        ext = (x0, x1, y - h / 2, y + h / 2)
        grad = np.linspace(0, 1, 64)[None, :]
    else:
        pts = [(y - sh, x0), (y - sh, x1 + hd), (y - h / 2, x1 + hd), (y, x1), (y + h / 2, x1 + hd), (y + sh, x1 + hd), (y + sh, x0)]
        ext = (y - h / 2, y + h / 2, x1, x0)
        grad = np.linspace(0, 1, 64)[:, None]
    poly = Polygon(pts, closed=True, fc="none", ec="#4D4D4D", lw=1.1, zorder=z + 1)
    ax.add_patch(poly)
    base = np.array(to_rgb(color))
    img = (1 - 0.8 * grad[..., None]) * np.ones(3) + 0.8 * grad[..., None] * base
    # lighten start, tint end
    im = ax.imshow(np.clip(img, 0, 1), extent=ext, origin="upper" if not vertical else "upper", aspect="auto", zorder=z)
    im.set_clip_path(poly)


def tokens(ax, x, y, syms, w, h, fills, fs, ec="#272727", lw=1.0, colors=None):
    """Monospace strip: one outlined cell per symbol, letter-spaced."""
    for k, s in enumerate(syms):
        ax.add_patch(Rectangle((x + k * w, y), w, h, fc=fills[k], ec=ec, lw=lw, zorder=3))
        ax.text(x + (k + .5) * w, y + h / 2 - 0.004, s, ha="center", va="center", fontsize=fs, zorder=4,
                color=(colors[k] if colors else "#272727"), **{"family": MONO["family"], "weight": "bold"})


def trapezoid(ax, x, y, w, h, fc, flip=False, lw=1.1, z=3):
    """Encoder-like trapezoid (wide left, narrow right); flip for a decoder."""
    a, b = h * 0.5, h * 0.18
    pts = [(x, y), (x + w, y + (h - 2 * b) / 2 + 0 * a), (x + w, y + h - (h - 2 * b) / 2), (x, y + h)]
    if flip:
        pts = [(x + w - px + x, py) for px, py in pts]
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec="#272727", lw=lw, zorder=z))


def arrow(ax, p, q, col="#272727", lw=1.0, rad=0.0, style="-|>", ms=7, ls="-", z=5):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, lw=lw, color=col, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0, zorder=z))
