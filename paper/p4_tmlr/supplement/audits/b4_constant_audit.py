"""Exact B=4 endpoint certificate arithmetic for the r,g rectangle.

The script verifies the finite history enumeration and rational constants.
The analytic posterior envelope and witness are written in task.md/local-proof.md.
"""
from fractions import Fraction as F
from itertools import product

r, g = F(1, 100), F(1, 2)
g0, g1 = 1/(1-r**2), r/(1-r**2)  # normalized G_y/(g r)
v = 1/(2*(1-r))               # normalized v1/(g r)
delta = g*(3*r+2*r**2+r**3) + g**2*r**2
dstar = 1-delta
error = {
    2: g*r**2/(1-r),
    3: (g*(r**2+r**3)+g**2*r**2)/(1-r),
    4: (g*(r**2+r**3+r**4)+g**2*(2*r**2+2*r**3))/(1-r),
}
E = {m: (g0*delta+error[m]/(g*r))/dstar for m in range(2,5)}
Dmax = [F(1), F(1), 1+g*r,
        1+g*(2*r+r**2),
        1+g*(3*r+2*r**2+r**3)+g**2*r**2]

rows=[]
for m in range(5):
    for ys in product((0,1), repeat=m):
        z=ys.count(0)
        value=(4*v if m==0 else
               (g0 if ys[-1]==0 else g1)+3*v if m==1 else
               (g0 if ys[-1]==0 else g1)+E[m]+(4-m)*v)
        causal=5*Dmax[m]*value/(5-m+2*z)
        iid=Dmax[m]*value
        rows.append((m,''.join(map(str,ys)) or '-',z,value,causal,iid))

max_c=max(row[4] for row in rows)
max_i=max(row[5] for row in rows)
assert delta == F(30251, 2000000)
assert dstar == F(1969749, 2000000)
assert max_c < F(210,100)   # 2.10
assert max_i < F(252,100)   # 2.52

print('m history z V/(gr) causal/(gr) iid/(gr)')
for row in rows:
    print(*row)
print('D_* =',dstar)
print('E_m/(gr) =',E)
print('max causal =',max_c, float(max_c))
print('max IID =',max_i, float(max_i))
