"""Glyphs for the Paper 1 composed figures, after the figures4papers "Miscellaneous" examples
(VIGIL robots/scales/banners, RNAGenScape standard-vs-ours, Dispersion block-arrow banner, ImmunoStruct braces).
Adds drawing methods to svgkit.Svg. Semantic colours (used in every figure):
  deployed policy = orange, reference policy = blue, label/coin = gold, paired cost/scales = green,
  uniform (standard) = red, gated (ours) = blue, harm/alarm = dark red.
"""
from svgkit import C, MONO, SANS, SERIF, Svg, shade  # noqa: F401

SEM = dict(deployed="#D9763A", deployed_l="#F7DCC8", reference="#2F6DB5", reference_l="#CFE3F6",
           cost="#4E8A3E", cost_l="#DDF0D2", uniform="#B64342", uniform_l="#F6CFCB", ours="#0F4D92",
           alarm="#8B1E1E", coin="#E0A92B", grey_l="#EDECEC", grey_m="#BDBCBC", magenta="#C2318F")


def robot(S: Svg, x, y, s, col, label=None, lcol=None, size=9.6):
    """Rounded-head robot (VIGIL MLLM icon). (x, y) is the top-left of the glyph box of width s."""
    h = s * 0.95
    S.path("M%g,%g L%g,%g" % (x + s / 2, y, x + s / 2, y + s * 0.14), stroke=col, sw=1.6)
    S.circle(x + s / 2, y - 1, s * 0.07, fill=col, stroke=col)
    S.rect(x + s * 0.12, y + s * 0.14, s * 0.76, s * 0.52, fill="#FFFFFF", stroke=col, sw=1.8, rx=s * 0.16)
    S.circle(x + s * 0.34, y + s * 0.38, s * 0.07, fill=col, stroke=col)
    S.circle(x + s * 0.66, y + s * 0.38, s * 0.07, fill=col, stroke=col)
    S.path("M%g,%g L%g,%g" % (x + s * 0.38, y + s * 0.55, x + s * 0.62, y + s * 0.55), stroke=col, sw=1.2)
    S.rect(x + s * 0.2, y + s * 0.7, s * 0.6, s * 0.25, fill="#FFFFFF", stroke=col, sw=1.6, rx=s * 0.06)
    S.rect(x + s * 0.04, y + s * 0.34, s * 0.07, s * 0.2, fill=col, stroke=None, rx=1.5)
    S.rect(x + s * 0.89, y + s * 0.34, s * 0.07, s * 0.2, fill=col, stroke=None, rx=1.5)
    if label:
        S.text(x + s / 2, y + h + size + 1, label, size=size, family=MONO, weight="bold", fill=lcol or col, anchor="middle")


def scales(S: Svg, x, y, s, col=None, label=None, size=9.6):
    """Balance scales (reward model / paired cost)."""
    col = col or SEM["cost"]
    cx = x + s / 2
    S.path("M%g,%g L%g,%g" % (cx, y + s * 0.12, cx, y + s * 0.88), stroke=col, sw=1.8)
    S.path("M%g,%g L%g,%g" % (x + s * 0.12, y + s * 0.26, x + s * 0.88, y + s * 0.26), stroke=col, sw=1.8)
    S.path("M%g,%g L%g,%g" % (cx - s * 0.2, y + s * 0.88, cx + s * 0.2, y + s * 0.88), stroke=col, sw=2.2)
    for px in (x + s * 0.16, x + s * 0.84):
        S.path("M%g,%g L%g,%g M%g,%g L%g,%g" % (px, y + s * 0.26, px - s * 0.1, y + s * 0.5, px, y + s * 0.26, px + s * 0.1, y + s * 0.5),
               stroke=col, sw=1)
        S.path("M%g,%g Q%g,%g %g,%g Z" % (px - s * 0.14, y + s * 0.5, px, y + s * 0.64, px + s * 0.14, y + s * 0.5), fill=SEM["cost_l"], stroke=col, sw=1.2)
    S.circle(cx, y + s * 0.1, s * 0.05, fill=col, stroke=col)
    if label:
        S.text(cx, y + s + size, label, size=size, family=MONO, weight="bold", fill=col, anchor="middle")


def doc(S: Svg, x, y, w, h, col="#272727", fill="#FFFFFF", nlines=3, sw=1.6):
    """A document / event card with text lines (VIGIL text icon)."""
    S.rect(x, y, w, h, fill=fill, stroke=col, sw=sw, rx=3)
    for k in range(nlines):
        yy = y + h * (0.24 + 0.52 * k / max(nlines - 1, 1))
        S.path("M%g,%g L%g,%g" % (x + w * 0.16, yy, x + w * (0.84 if k < nlines - 1 else 0.55), yy), stroke=col, sw=1.1)


def cross(S: Svg, x, y, s=9, col="#C23B3B", sw=2.4):
    S.path("M%g,%g L%g,%g M%g,%g L%g,%g" % (x - s / 2, y - s / 2, x + s / 2, y + s / 2, x - s / 2, y + s / 2, x + s / 2, y - s / 2), stroke=col, sw=sw)


def check(S: Svg, x, y, s=9, col="#3FA34D", sw=2.6):
    S.path("M%g,%g L%g,%g L%g,%g" % (x - s * 0.5, y, x - s * 0.1, y + s * 0.4, x + s * 0.55, y - s * 0.45), stroke=col, sw=sw)


def pill_banner(S: Svg, x, y, w, h, text_rich, kind="grey", size=11):
    """Statement banner: dashed grey (problem) or solid blue tint (our fix), as in VIGIL (a)."""
    if kind == "grey":
        S.rect(x, y, w, h, fill="#F4F4F4", stroke="#272727", sw=1.4, rx=h * 0.28, dash="5 3")
    else:
        S.rect(x, y, w, h, fill="#DDEBFA", stroke=None, rx=h * 0.28)
    S.text(x + w / 2, y + h / 2 + size * 0.34, text_rich, size=size, anchor="middle", fill=SEM["ours"] if kind != "grey" else "#272727")


def banner_arrow(S: Svg, x, y, w, h, text_rich, color="#A9C9E8", size=12):
    """Full-width gradient block arrow carrying the takeaway (Dispersion observation)."""
    hd = h * 0.62
    pts = [(x, y + h * 0.18), (x + w - hd, y + h * 0.18), (x + w - hd, y), (x + w, y + h / 2), (x + w - hd, y + h),
           (x + w - hd, y + h * 0.82), (x, y + h * 0.82)]
    g = S.grad("#FFFFFF", color, 1, 0)
    S.poly(pts, fill=g, stroke=None)
    S.text(x + (w - hd) / 2, y + h / 2 + size * 0.34, text_rich, size=size, anchor="middle")


def brace_left(S: Svg, x, y0, y1, w=8, col="#272727", sw=1.3):
    """Curly brace '{' spanning y0..y1 at x (point to the left)."""
    ym = (y0 + y1) / 2
    d = (f"M{x + w},{y0} Q{x},{y0} {x},{y0 + w} L{x},{ym - w} Q{x},{ym} {x - w},{ym} "
         f"Q{x},{ym} {x},{ym + w} L{x},{y1 - w} Q{x},{y1} {x + w},{y1}")
    S.path(d, stroke=col, sw=sw)


def brace_down(S: Svg, x0, x1, y, h=7, col="#272727", sw=1.3):
    """Curly brace spanning x0..x1 below a group (point downward)."""
    xm = (x0 + x1) / 2
    d = (f"M{x0},{y} Q{x0},{y + h} {x0 + h},{y + h} L{xm - h},{y + h} Q{xm},{y + h} {xm},{y + h * 1.9} "
         f"Q{xm},{y + h} {xm + h},{y + h} L{x1 - h},{y + h} Q{x1},{y + h} {x1},{y}")
    S.path(d, stroke=col, sw=sw)


def eq_box(S: Svg, x, y, w, h, fill, stroke, parts, size=10.5):
    """Rounded equation box. parts = list of (text_rich, fill_colour or None); laid out centred in one line."""
    S.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.5, rx=8)
    return (x + w / 2, y + h / 2 + size * 0.34)


def purse(S: Svg, x, y, s=22, col="#E0A92B"):
    """Coin purse / budget bag."""
    S.path("M%g,%g Q%g,%g %g,%g Q%g,%g %g,%g Z" % (x, y + s * 0.5, x - s * 0.1, y + s * 1.05, x + s * 0.5, y + s * 1.05,
                                                    x + s * 1.1, y + s * 1.05, x + s, y + s * 0.5), fill="#F6E3A8", stroke="#8A6A12", sw=1.2, shadow=True)
    S.path("M%g,%g L%g,%g L%g,%g L%g,%g" % (x + s * 0.2, y + s * 0.5, x + s * 0.3, y + s * 0.18, x + s * 0.7, y + s * 0.18, x + s * 0.8, y + s * 0.5), fill="#F6E3A8", stroke="#8A6A12", sw=1.2)
    S.text(x + s / 2, y + s * 0.88, "$", size=s * 0.5, weight="bold", anchor="middle", fill="#6A4F0C")


def mini_battery(S: Svg, x, y, w, h, frac, col, label=None, size=9):
    S.rect(x, y, w, h, fill="#FFFFFF", stroke="#272727", sw=1.2, rx=2.5)
    S.rect(x + w, y + h * 0.3, 2.6, h * 0.4, fill="#272727", stroke=None)
    if frac > 0:
        S.rect(x + 1.5, y + 1.5, (w - 3) * frac, h - 3, fill=col, stroke=None, rx=1.5)
    if label:
        S.text(x + w + 6, y + h / 2 + size * 0.33, label, size=size, fill="#4D4D4D")
