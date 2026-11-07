"""Exact lower/upper bounds on the calendar-mixture value conv(C*) from grid values.

Each C_c is convex and nonincreasing in the risk level a (LP value function), so on a grid
interval [a_k, a_{k+1}] it lies above: the right endpoint value; the left neighbour secant
extended from a_k; the right neighbour secant extended back from a_{k+1}. The lower hull of the
vertices of these per-calendar bounding functions lower-bounds conv(min_c C_c); the lower hull
of the grid points upper-bounds it (13_A2_BRANCH_CONFLICT_THEORY.md, Remark 1).
"""

from fractions import Fraction as F
from itertools import pairwise


def lower_hull(points):
    best = {}
    for x, y in points:
        best[x] = min(y, best.get(x, y))
    hull = []
    for p in sorted(best.items()):
        while (
            len(hull) >= 2
            and (hull[-1][0] - hull[-2][0]) * (p[1] - hull[-2][1])
            - (hull[-1][1] - hull[-2][1]) * (p[0] - hull[-2][0])
            <= 0
        ):
            hull.pop()
        hull.append(p)
    return hull


def hull_value(hull, x):
    """Value of the lower envelope at x, allowing any vertex at a <= x (smaller risk is feasible)."""
    best = min(y for a, y in hull if a <= x)
    for (x0, y0), (x1, y1) in pairwise(hull):
        if x0 <= x <= x1:
            best = min(best, y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return best


def bound_points(values):
    """values: sorted list of (a, C_c(a)) for one calendar -> vertices of its lower bound L_c."""
    xs = [a for a, _ in values]
    ys = [y for _, y in values]
    n = len(xs)
    slope = [(ys[k + 1] - ys[k]) / (xs[k + 1] - xs[k]) for k in range(n - 1)]
    pts = list(values)
    for k in range(n - 1):
        lo, hi = xs[k], xs[k + 1]
        lines = [(F(0), ys[k + 1])]  # y = m*x + b; monotone floor
        if k >= 1:
            lines.append((slope[k - 1], ys[k] - slope[k - 1] * xs[k]))
        if k + 1 < n - 1:
            lines.append((slope[k + 1], ys[k + 1] - slope[k + 1] * xs[k + 1]))

        def L(x, lines=lines):
            return max(m * x + b for m, b in lines)

        cand = {lo, hi}
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                (m1, b1), (m2, b2) = lines[i], lines[j]
                if m1 != m2:
                    x = (b2 - b1) / (m1 - m2)
                    if lo < x < hi:
                        cand.add(x)
        pts.extend((x, L(x)) for x in cand if x not in (lo, hi))
        # the bound at interior points may exceed the chord; endpoints stay exact grid values
    return pts


def mixture_bounds(per_calendar, target):
    """per_calendar: {cal: [(a, cost), ...]} -> (lower, upper) bounds on conv(min_c C_c)(target)."""
    up = lower_hull([p for vals in per_calendar.values() for p in vals])
    lo = lower_hull([p for vals in per_calendar.values() for p in bound_points(sorted(vals))])
    return hull_value(lo, target), hull_value(up, target)
