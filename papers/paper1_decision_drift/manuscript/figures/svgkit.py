"""Tiny SVG composer for the composed schematics (figures4papers "Miscellaneous" look).

Units: 1 user unit = 1 CSS px; the figure is exported at 6.5 in = 624 px, so 1 unit = 0.75 pt in the paper
(minimum text 9.4 units = 7 pt).  Text stays <text> (Helvetica), assets are embedded base64 <image>.
Export: Chrome headless (PNG via --screenshot, PDF via --print-to-pdf on an HTML wrapper); see README.
"""
import base64
import re
import subprocess
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SANS = "Helvetica, Arial, sans-serif"
MONO = "'Courier New', Courier, monospace"
SERIF = "'Times New Roman', Times, serif"

C = dict(blue_main="#0F4D92", blue2="#3775BA", red="#B64342", dred="#8B1E1E", pink="#F6CFCB", blue="#CFE3F6",
         grey="#E3E2E2", lav="#E6DAEE", butter="#FCEFC7", sage="#DDE5C8", green="#2E6B2E", green_l="#DDF3DE",
         green2="#8BCF8B", ink="#272727", mid="#4D4D4D", neutral="#CFCECE", gtxt="#767676", dblue="#1B3A6B",
         dlav="#4B2A6B", dsage="#3E5A2A", gold="#C8A02A")


def esc(s):
    return s.replace("&", "&amp;")


def rich(s):
    """<sub>, <sup>, <i>, <b>, <m> (mono), <c r> (colour) markup -> tspans."""
    s = esc(s)
    s = s.replace("<sub>", '<tspan baseline-shift="sub" font-size="72%">').replace("</sub>", "</tspan>")
    s = s.replace("<sup>", '<tspan baseline-shift="super" font-size="72%">').replace("</sup>", "</tspan>")
    s = s.replace("<i>", '<tspan font-style="italic" font-family="%s">' % SERIF).replace("</i>", "</tspan>")
    s = s.replace("<b>", '<tspan font-weight="bold">').replace("</b>", "</tspan>")
    s = s.replace("<m>", '<tspan font-family="%s" font-weight="bold">' % MONO).replace("</m>", "</tspan>")
    s = re.sub(r"<c ([#\w]+)>", lambda m: '<tspan fill="%s">' % (C.get(m.group(1), m.group(1))), s).replace("</c>", "</tspan>")
    return s


class Svg:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.defs, self.body, self._gid = [], [], 0
        self.defs.append('<filter id="sh" x="-20%" y="-20%" width="150%" height="160%"><feGaussianBlur in="SourceAlpha" stdDeviation="1.3"/>'
                         '<feOffset dx="1" dy="1.4" result="b"/><feComponentTransfer><feFuncA type="linear" slope="0.28"/></feComponentTransfer>'
                         '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
        self.defs.append('<filter id="soft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.2"/></filter>')
        self.defs.append('<marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
                         '<path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker>')

    # ---- plumbing -------------------------------------------------------------------------------
    def add(self, s):
        self.body.append(s)

    def grad(self, c0, c1, x1=1, y1=0, stops=None):
        self._gid += 1
        gid = "g%d" % self._gid
        st = stops or [(0, c0), (1, c1)]
        self.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="%s" y2="%s">%s</linearGradient>' % (
            gid, x1, y1, "".join('<stop offset="%s" stop-color="%s"/>' % (o, c) for o, c in st)))
        return "url(#%s)" % gid

    def image(self, x, y, w, h, path, opacity=1.0, mime="image/png"):
        b = base64.b64encode(Path(path).read_bytes()).decode()
        self.add('<image x="%g" y="%g" width="%g" height="%g" opacity="%g" href="data:%s;base64,%s"/>' % (x, y, w, h, opacity, mime, b))

    def text(self, x, y, s, size=10, weight="normal", fill=None, anchor="start", family=SANS, style="normal", ls=None, extra=""):
        fill = C.get(fill, fill) if fill else C["ink"]
        self.add('<text x="%g" y="%g" font-size="%g" font-weight="%s" fill="%s" text-anchor="%s" font-family="%s" font-style="%s"%s %s>%s</text>' % (
            x, y, size, weight, fill, anchor, family, style, (' letter-spacing="%g"' % ls) if ls else "", extra, rich(s)))

    def lines(self, x, y, lst, dy=11, **kw):
        for i, s in enumerate(lst):
            self.text(x, y + i * dy, s, **kw)

    # ---- shapes ---------------------------------------------------------------------------------
    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1, rx=0, dash=None, shadow=False, opacity=1.0):
        f = C.get(fill, fill)
        st = C.get(stroke, stroke) if stroke else "none"
        self.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-width="%g"%s%s%s/>' % (
            x, y, w, h, rx, f, st, sw, (' stroke-dasharray="%s"' % dash) if dash else "", ' filter="url(#sh)"' if shadow else "",
            (' opacity="%g"' % opacity) if opacity != 1 else ""))

    def poly(self, pts, fill="none", stroke="#272727", sw=1, shadow=False, opacity=1.0, dash=None):
        f = C.get(fill, fill)
        self.add('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%g"%s%s%s/>' % (
            " ".join("%g,%g" % p for p in pts), f, C.get(stroke, stroke) if stroke else "none", sw,
            ' filter="url(#sh)"' if shadow else "", (' opacity="%g"' % opacity) if opacity != 1 else "",
            (' stroke-dasharray="%s"' % dash) if dash else ""))

    def path(self, d, fill="none", stroke="#272727", sw=1, dash=None, marker=False, marker_start=False, opacity=1.0, shadow=False, cap="round"):
        self.add('<path d="%s" fill="%s" stroke="%s" stroke-width="%g" stroke-linecap="%s" stroke-linejoin="round"%s%s%s%s%s/>' % (
            d, C.get(fill, fill), C.get(stroke, stroke) if stroke else "none", sw, cap,
            (' stroke-dasharray="%s"' % dash) if dash else "", ' marker-end="url(#ah)"' if marker else "",
            ' marker-start="url(#ah)"' if marker_start else "", (' opacity="%g"' % opacity) if opacity != 1 else "",
            ' filter="url(#sh)"' if shadow else ""))

    def circle(self, x, y, r, fill="none", stroke="#272727", sw=1, shadow=False, opacity=1.0):
        self.add('<circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="%g"%s%s/>' % (
            x, y, r, C.get(fill, fill), C.get(stroke, stroke) if stroke else "none", sw,
            ' filter="url(#sh)"' if shadow else "", (' opacity="%g"' % opacity) if opacity != 1 else ""))

    def arrow(self, pts, col="ink", sw=1, dash=None, both=False):
        """Thin connector through pts (list of (x,y)); orthogonal if the caller gives the corners."""
        d = "M" + " L".join("%g,%g" % p for p in pts)
        self.add('<path d="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linejoin="round"%s marker-end="url(#ah)"%s/>' % (
            d, C.get(col, col), sw, (' stroke-dasharray="%s"' % dash) if dash else "", ' marker-start="url(#ah)"' if both else ""))

    def curve(self, p, q, bend, col="ink", sw=1, dash=None, both=False):
        """Quadratic curve p->q with control offset 'bend' (perpendicular)."""
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        dx, dy = q[0] - p[0], q[1] - p[1]
        n = (dx ** 2 + dy ** 2) ** .5 or 1
        cx, cy = mx - dy / n * bend, my + dx / n * bend
        self.add('<path d="M%g,%g Q%g,%g %g,%g" fill="none" stroke="%s" stroke-width="%g"%s marker-end="url(#ah)"%s/>' % (
            p[0], p[1], cx, cy, q[0], q[1], C.get(col, col), sw, (' stroke-dasharray="%s"' % dash) if dash else "",
            ' marker-start="url(#ah)"' if both else ""))

    # ---- composite glyphs -----------------------------------------------------------------------
    def block_arrow(self, x0, y, x1, h, color, vertical=False):
        """Shaded block arrow: white -> tint gradient, grey outline, drop shadow (ImmunoStruct style)."""
        L = abs(x1 - x0)
        hd = min(L * 0.5, h * 0.7)
        sh = h * 0.27
        if not vertical:
            pts = [(x0, y - sh), (x1 - hd, y - sh), (x1 - hd, y - h / 2), (x1, y), (x1 - hd, y + h / 2), (x1 - hd, y + sh), (x0, y + sh)]
            g = self.grad("#FFFFFF", color, 1, 0)
        else:  # x0 = top y, x1 = bottom y, y = centre x
            pts = [(y - sh, x0), (y - sh, x1 - hd), (y - h / 2, x1 - hd), (y, x1), (y + h / 2, x1 - hd), (y + sh, x1 - hd), (y + sh, x0)]
            g = self.grad("#FFFFFF", color, 0, 1)
        self.poly(pts, fill=g, stroke="#4D4D4D", sw=0.8, shadow=True)

    def trapezoid(self, x, y, w, h, fill, flip=False, letter=None, size=13, lw=1):
        a = h * 0.2
        pts = [(x, y), (x + w, y + a), (x + w, y + h - a), (x, y + h)]
        if flip:
            pts = [(x + w - (px - x), py) for px, py in pts]
        g = self.grad("#FFFFFF", fill, 0.2, 1)
        self.poly(pts, fill=g, stroke="ink", sw=lw, shadow=True)
        if letter:
            self.text(x + w * (0.42 if not flip else 0.58), y + h / 2 + size * 0.34, letter, size=size, anchor="middle")

    def sphere(self, x, y, r, color, light="#FFFFFF"):
        self._gid += 1
        gid = "s%d" % self._gid
        self.defs.append('<radialGradient id="%s" cx="0.36" cy="0.32" r="0.75" fx="0.3" fy="0.26"><stop offset="0" stop-color="%s"/>'
                         '<stop offset="0.35" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>' % (
                             gid, light, color, shade(color, 0.62)))
        self.circle(x, y, r, fill="url(#%s)" % gid, stroke="ink", sw=0.9, shadow=True)

    def tokens(self, x, y, syms, w, h, fills, size=10, opacity=None, bold=True):
        for k, s in enumerate(syms):
            op = opacity[k] if opacity else 1
            self.rect(x + k * w, y, w, h, fill=fills[k], stroke="ink", sw=0.9, opacity=op)
            self.text(x + (k + .5) * w, y + h / 2 + size * 0.33, s, size=size, anchor="middle", family=MONO,
                      weight="bold" if bold else "normal", extra=(' opacity="%g"' % op) if op != 1 else "")

    def group_box(self, x, y, w, h, title, tcolor, dash="5 3", sw=1.3, tsize=11.5, tpos="top", tx=None, rx=10):
        self.rect(x, y, w, h, fill="none", stroke="ink", sw=sw, rx=rx, dash=dash)
        ty = y - 3 if tpos == "top" else y + h + tsize
        # white cut so the title sits on the dashed line
        tw = len(title) * tsize * 0.55 + 8
        tx = x + 14 if tx is None else tx
        self.rect(tx, y - tsize * 0.62, tw, tsize * 1.1, fill="#FFFFFF")
        self.text(tx + 4, y + tsize * 0.32, title, size=tsize, weight="bold", fill=tcolor)

    def note(self, x, y, w, h, fill, lines, size=9.6, rx=7, stroke=None, bullet=True, fcol="ink", dy=None):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=0.8, rx=rx)
        dy = dy or size * 1.18
        for i, s in enumerate(lines):
            self.text(x + 6, y + size + 4 + i * dy, ("➤ " if bullet else "") + s, size=size, style="normal", fill=fcol)

    def callout(self, x, y, w, h, fill, rx=9):
        self.rect(x, y, w, h, fill=fill, rx=rx, opacity=1)

    def coin(self, x, y, r=5, label=None):
        g = self.grad("#FFF2B0", "#D9A82A", 1, 1)
        self.circle(x, y, r, fill=g, stroke="#8A6A12", sw=0.8, shadow=True)
        self.circle(x, y, r * 0.66, fill="none", stroke="#8A6A12", sw=0.5)
        if label:
            self.text(x, y + r * 0.36, label, size=r * 1.1, weight="bold", anchor="middle", fill="#6A4F0C")

    def shield(self, x, y, s, fill="#CFE3F6", stroke="#1B3A6B"):
        d = "M%g,%g L%g,%g L%g,%g Q%g,%g %g,%g Q%g,%g %g,%g L%g,%g Z" % (
            x, y, x + s, y, x + s, y + s * .55, x + s, y + s * 1.05, x + s / 2, y + s * 1.3,
            x, y + s * 1.05, x, y + s * .55, x, y)
        self.path(d, fill=fill, stroke=stroke, sw=1)
        self.path("M%g,%g L%g,%g L%g,%g" % (x + s * .25, y + s * .52, x + s * .44, y + s * .74, x + s * .76, y + s * .28), stroke="#2E6B2E", sw=1.6)

    def die(self, x, y, s, fill="#FFFFFF"):
        self.rect(x, y, s, s, fill=fill, stroke="ink", sw=0.9, rx=s * .22)
        for px, py in ((.28, .28), (.72, .28), (.5, .5), (.28, .72), (.72, .72)):
            self.circle(x + px * s, y + py * s, s * .075, fill="ink", stroke=None)

    def inline_svg(self, x, y, w, h, svg_text):
        """Embed a matplotlib-made SVG (svg.fonttype none, so text stays text) as a nested <svg>."""
        m = re.search(r"<svg[^>]*viewBox=\"([^\"]+)\"[^>]*>(.*)</svg>", svg_text, re.S)
        vb, inner = m.group(1), m.group(2)
        self.add('<svg x="%g" y="%g" width="%g" height="%g" viewBox="%s" preserveAspectRatio="xMinYMin meet">%s</svg>' % (x, y, w, h, vb, inner))

    # ---- output ---------------------------------------------------------------------------------
    def svg(self):
        return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%g" height="%g" viewBox="0 0 %g %g">'
                '<defs>%s</defs><rect width="%g" height="%g" fill="#FFFFFF"/>%s</svg>' % (
                    self.w, self.h, self.w, self.h, "".join(self.defs), self.w, self.h, "".join(self.body)))

    def save(self, stem):
        stem = Path(stem)
        stem.with_suffix(".svg").write_text(self.svg())
        bdir = stem.parent / "_build"
        bdir.mkdir(exist_ok=True)
        html_path = bdir / (stem.name + ".html")
        html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:%gpx %gpx;margin:0}html,body{margin:0;padding:0;background:#fff}'
                'svg{display:block}</style></head><body>%s</body></html>' % (self.w, self.h, self.svg()))
        html_path.write_text(html)
        run = lambda args: subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox"] + args,
                                         check=True, capture_output=True)
        run(["--screenshot=%s" % stem.with_suffix(".png"), "--window-size=%d,%d" % (self.w, self.h), "--force-device-scale-factor=4",
             "file://%s" % html_path])
        run(["--print-to-pdf=%s" % stem.with_suffix(".pdf"), "--no-pdf-header-footer", "file://%s" % html_path])


def shade(hexcol, f):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r * f), int(g * f), int(b * f))
