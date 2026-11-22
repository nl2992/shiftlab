"""Exact conservative B=6 endpoint enumeration based on HMM spin moments."""
from fractions import Fraction as F
from itertools import combinations, product

B=6
r,g=F(1,100),F(1,2)
def moment_exponent(indices):
    return sum(indices[i+1]-indices[i] for i in range(0,len(indices),2))
def density_delta(m):
    return sum(g**(len(J)//2)*r**moment_exponent(J)
               for k in range(2,m+1,2) for J in combinations(range(1,m+1),k))
def posterior_error(m):
    singleton=sum(g*r**(m-i+1) for i in range(1,m))/(1-r)
    higher=F(0)
    for k in range(3,m+1,2):
        for J in combinations(range(1,m+1),k):
            paired=sum(J[i+1]-J[i] for i in range(0,k-1,2))
            exponent=paired + (m-J[-1]+1)
            higher += g**((k+1)//2)*r**exponent/(1-r)
    return singleton+higher
deltas=[density_delta(m) for m in range(B+1)]
delta=deltas[B]; dstar=1-delta
g0,g1=1/(1-r**2),r/(1-r**2)
v=1/(2*(1-r))
E={m:(g0*delta+posterior_error(m)/(g*r))/dstar for m in range(2,B+1)}
Dmax=[1+x for x in deltas]
rows=[]
for m in range(B+1):
    for ys in product((0,1),repeat=m):
        z=ys.count(0)
        val=(B*v if m==0 else
             (g0 if ys[-1]==0 else g1)+(B-1)*v if m==1 else
             (g0 if ys[-1]==0 else g1)+E[m]+(B-m)*v)
        causal=(B+1)*Dmax[m]*val/(B+1-m+2*z)
        iid=Dmax[m]*val
        rows.append((m,''.join(map(str,ys)) or '-',z,val,causal,iid))
maxc=max(row[4] for row in rows); maxi=max(row[5] for row in rows)
assert dstar>F(97,100)
assert maxc<F(310,100) # 3.10
assert maxi<F(354,100) # 3.54
print('m history z V/(gr) causal/(gr) iid/(gr)')
for row in rows: print(*row)
print('delta_m =',deltas)
print('D_* =',dstar)
print('E_m/(gr) =',E)
print('max causal =',maxc,float(maxc))
print('max IID =',maxi,float(maxi))
