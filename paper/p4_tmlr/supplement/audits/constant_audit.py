"""Exact corner arithmetic for the proposed B=3 pathwise certificate.

This checks only the finite enumeration and constants at (r,g)=(1/100,1/2).
It does not establish monotonicity over the open rectangle or prove the
posterior/value envelope used to form the table.
"""
from fractions import Fraction as F
from itertools import product

r, g = F(1, 100), F(1, 2)
dstar = 1 - g * (2 * r + r**2)
G0 = g * r / (1 - r**2)
G1 = g * r**2 / (1 - r**2)
v1 = g * r / (2 * (1 - r))
E = (G0 * g * (2 * r + r**2)
     + g * (r**2 + r**3) / (1 - r)
     + g**2 * r**2 / (1 - r)) / dstar

rows = []
for m in range(4):
    for ys in product((0, 1), repeat=m):
        z = ys.count(0)
        D = 1 + g * sum(
            (2 * ys[i] - 1) * (2 * ys[j] - 1) * (-r) ** (j - i)
            for i in range(m) for j in range(i + 1, m)
        )
        q_lr = 4 * D / (4 - m + 2 * z)
        if m == 0:
            V = 3 * v1
        elif m == 1:
            V = (G0 if ys[-1] == 0 else G1) + 2 * v1
        else:
            V = (G0 if ys[-1] == 0 else G1) + E + (3 - m) * v1
        causal = q_lr * V / (g * r)
        iid = D * V / (g * r)
        rows.append((m, ''.join(map(str, ys)) or '-', z, D, q_lr, V/(g*r), causal, iid))

assert dstar == F(19799, 20000)
assert E/(g*r) < F(26, 1000)
assert G0/(g*r) < F(100011, 100000)
assert G1/(g*r) < F(1001, 100000)
assert v1/(g*r) < F(50506, 100000)
assert max(row[6] for row in rows) < F(161, 100)
assert max(row[7] for row in rows) < F(202, 100)

# Uniform envelope over the whole rectangle: each normalized value bound and
# each likelihood-ratio numerator is increasing in r,g. Bound D_m separately
# by m, using gaps >=1, then enumerate all binary histories exactly.
delta = [F(1), F(1), 1 + g * r, 1 + g * (2 * r + r**2)]
g0_bar, g1_bar = 1 / (1-r**2), r / (1-r**2)  # G_y/(g r)
v_bar = 1 / (2 * (1-r))                    # v1/(g r)
e_bar = E / (g*r)
uniform_causal = []
uniform_iid = []
for m in range(4):
    for ys in product((0, 1), repeat=m):
        z = ys.count(0)
        val = (3*v_bar if m == 0 else
               (g0_bar if ys[-1] == 0 else g1_bar) + 2*v_bar if m == 1 else
               (g0_bar if ys[-1] == 0 else g1_bar) + e_bar + (3-m)*v_bar)
        uniform_causal.append(4*delta[m]*val/(4-m+2*z))
        uniform_iid.append(delta[m]*val)
assert max(uniform_causal) == F(5360, 3333) < F(161, 100)
assert max(uniform_iid) == F(6700, 3333) < F(202, 100)

print('m history z D_m Q-likelihood-ratio V/(gr) causal/(gr) iid/(gr)')
for m, history, z, D, q_lr, value, causal, iid in rows:
    print(m, history, z, D, q_lr, value, causal, iid)
print('E/(gr) =', E/(g*r))
print('max causal coefficient =', max(row[6] for row in rows))
print('max IID coefficient =', max(row[7] for row in rows))
print('uniform rectangle causal bound =', max(uniform_causal))
print('uniform rectangle IID bound =', max(uniform_iid))
