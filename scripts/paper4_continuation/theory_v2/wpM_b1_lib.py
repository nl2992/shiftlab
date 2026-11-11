"""WP-M (P1): closed forms for the B = 1 relative premium rho_Gamma = Gamma / (C0 - V*_IID).

Symmetric stationary anti-persistent chain, t in (1/2, 1), r = 2t - 1, emissions (e, 1 - e), prior 1/2,
g = (1 - 2e)^2, d odd, alpha <= 1/2 (N1).  See MIXING_PREMIUM_THEOREM.md, Theorem M1.

  rho_exact(T, d, r, g, c, k)  = Pi^+ / (Gbar_0 - 2c)    (Pi = SP1 numerator; 0 if Pi <= 0)
  rho_lower(d, r, g, c, k)     = c_1 (T-uniform lower bound of Theorem M1, valid when 2c + k < g r^d (1 - r))
  rho_limit_k0(d, r, g, c)     = lim_{T -> oo} rho for k = 0
"""

from __future__ import annotations

import os
import sys
from fractions import Fraction as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wpC_sym_lib import gbar_primitive, sp1_exact  # noqa: E402


def rho_exact(T, d, r, g, c, k):
    if T <= d or d % 2 == 0:
        return F(0)
    pi = sp1_exact(T, d, r, g, c, k)
    if pi <= 0:
        return F(0)
    G0, _ = gbar_primitive(T, d, r, g, k)
    return pi / (G0 - 2 * c)


def rho_lower(d, r, g, c, k):
    """c_1 = [g r^d - 2c - max(k, g r^{d+1} - k)] / (2 (k + g r^d / (1 - r^2) - 2c)); None if outside region."""
    if not (d % 2 == 1 and 0 < r < 1 and 2 * c + k < g * r**d * (1 - r)):
        return None
    num = g * r**d - 2 * c - max(k, g * r ** (d + 1) - k)
    den = 2 * (k + g * r**d / (1 - r**2) - 2 * c)
    return num / den


def rho_limit_k0(d, r, g, c):
    num = g * r**d / (2 * (1 + r)) - c
    if num <= 0:
        return F(0)
    return num / (g * r**d / (1 - r**2) - 2 * c)
