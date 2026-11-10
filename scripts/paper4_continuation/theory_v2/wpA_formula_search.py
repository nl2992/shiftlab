"""Formula-only (own N1 implementation) red-team: static cells (S1) and TP2+(M) cells (Z1)."""
import sys, random, json
sys.path.insert(0,'scripts/paper4_continuation/theory_v2')
from wpA_audit_checks import B1Model, n1_formula
from fractions import Fraction as F
mode, seed, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rng = random.Random(seed); hits=[]; cnt=0; tried=0
def rf(lo,hi):
    while True:
        den=rng.choice([7,10,13,20,50,100]); v=F(rng.randint(0,den),den)
        if lo<v<hi: return v
while cnt < n:
    tried+=1
    T=rng.choice([2,3,4,5,6]); d=rng.choice([1,2,3])
    e0=rf(0,F(1,2)); e1=rf(F(1,2),1); prior=rng.choice([F(0),F(1),rf(0,1)])
    if mode=='static': t01=t10=F(0)
    else:
        t01=rf(-1,1) if rng.random()<.8 else F(0); t10=rf(-1,1-t01) if 1-t01>0 else F(0)
        if rng.random()<.1: t10=1-t01
    c=rng.choice([F(0),F(1,100),F(1,20)]); k=rng.choice([F(0),F(1,100),F(1,10),F(1,4)]); a=rng.choice([F(1,20),F(1,10),F(1,4),F(1,2)])
    m=B1Model(T,d,t01,t10,e0,e1,prior,c,k); f=n1_formula(m,a)
    D=f['designs']
    if mode=='tp2M':
        if not all(F(v['P1'])>=F(1,2) for v in D.values()): continue
    cnt+=1
    if f['Gamma']>0: hits.append([str(x) for x in (T,d,t01,t10,e0,e1,prior,c,k,a,f['Gamma'])])
print(json.dumps({'mode':mode,'seed':seed,'n':cnt,'tried':tried,'gamma_pos':len(hits),'hits':hits[:10]}))
