"""Analyze the frozen R5 alpha=.02 Round-5 follow-up without reselecting the operating point."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from bench2 import RISK_ALTS, RISK_NULLS

POLICIES = ["R5", "D2", "A5b", "gated_adaptive_range+front", "R:economic_stop"]

def wilson(k, n, z=1.96):
    p=k/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(max(0,center-half)),float(min(1,center+half))]

def ci(x):
    x=np.asarray(x, dtype=float)
    se=x.std(ddof=1)/np.sqrt(len(x)) if len(x)>1 else float('nan')
    return [float(x.mean()), float(x.mean()-1.96*se), float(x.mean()+1.96*se)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--out', required=True)
    a=ap.parse_args()
    df=pd.read_json(Path(a.input)/'records.jsonl', lines=True, precise_float=True)
    expected=set(RISK_NULLS+RISK_ALTS)
    assert set(df.regime)==expected, (set(df.regime), expected)
    assert set(df.policy)==set(POLICIES), set(df.policy)
    counts=df.groupby(['regime','policy']).size()
    assert (counts==100).all(), counts[counts!=100]
    assert set(df.seed)==set(range(100)), set(df.seed)
    assert df.groupby(['regime','policy','seed']).size().eq(1).all(), 'duplicate or missing paired row'
    out={'n_seeds_per_regime':100,'alpha':.02,'seed_base':2026110901,'regimes':{},'pooled':{}}
    for regime in RISK_NULLS:
        g=df[df.regime==regime]
        out['regimes'][regime]={p:{'promotions':int(g[g.policy==p].ever_promote.sum()),'n':len(g[g.policy==p]),'rate':float(g[g.policy==p].ever_promote.mean()),'wilson_95_ci':wilson(int(g[g.policy==p].ever_promote.sum()),len(g[g.policy==p]))} for p in POLICIES}
    # For each seed, average the six alternative regimes and retain the paired design.
    alt=df[df.regime.isin(RISK_ALTS)].groupby(['policy','seed']).net.mean().unstack('policy')
    for p in POLICIES:
        out['pooled'][p]={'alternative_net_cost_mean_ci':ci(alt[p])}
    out['paired_cost_differences_R5_minus_comparator']={p:ci(alt['R5']-alt[p]) for p in POLICIES if p!='R5'}
    out['alternative_cost_by_regime']={r:{p:ci(df[(df.regime==r)&(df.policy==p)].net) for p in POLICIES} for r in RISK_ALTS}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(out,indent=2)+'\n')
    lines=['# R5 Round-5 focused follow-up results','', 'Frozen alpha=0.02; 100 seeds per regime, seed base 2026110901. Values are descriptive mean and normal 95% t intervals over paired seeds, or empirical promotion counts.','', '## In-class null regimes','', '| Regime | ' + ' | '.join(POLICIES) + ' |','|'+'---|'*(len(POLICIES)+1)]
    for r,v in out['regimes'].items(): lines.append('| '+r+' | '+' | '.join(f"{v[p]['promotions']}/100 ({v[p]['rate']:.3f}, CI {v[p]['wilson_95_ci'][0]:.3f}–{v[p]['wilson_95_ci'][1]:.3f})" for p in POLICIES)+' |')
    lines += ['', '## Paired alternative cost contrasts', '', '| Comparator | R5 − comparator, mean [95% CI] |','|---|---:|']
    for p,v in out['paired_cost_differences_R5_minus_comparator'].items(): lines.append(f"| {p} | {v[0]:.2f} [{v[1]:.2f}, {v[2]:.2f}] |")
    lines += ['', 'Negative values favor R5 on net cost. Per-regime outcomes and source records are in the adjacent JSON and raw output directory. These simulator results do not establish an anytime validity guarantee or real-data transfer.','']
    Path(a.out).with_suffix('.md').write_text('\n'.join(lines))
    print('\n'.join(lines))
if __name__=='__main__': main()
