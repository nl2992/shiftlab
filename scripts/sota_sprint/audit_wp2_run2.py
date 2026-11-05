"""Recount stored WP2 Run-2 re-windowing records for decision-flag consistency."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUNS=sorted((ROOT/'outputs/sprint2/WP2').glob('run2*/records.jsonl'))
CS=5.0; CQ=.05

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path); a=ap.parse_args()
    rows=[]; errors=[]
    for path in RUNS:
        for lineno,line in enumerate(path.open(),1):
            r=json.loads(line); ps=r.get('promos',[]); tag=f'{path.parent.name}:{lineno}'
            if int(bool(ps)) != int(r['ever_promote']): errors.append(tag+': ever_promote')
            if len(ps) != int(r['n_promotions']): errors.append(tag+': n_promotions')
            expected_t=int(ps[0]['t']) if ps else -1
            if expected_t != int(r['first_deploy']): errors.append(tag+': first_deploy')
            for j,p in enumerate(ps):
                expected_ei=int(float(p['rest_sum'])-CS <= 0)
                if expected_ei != int(p['ei']): errors.append(tag+f': promo[{j}].ei')
            expected_net=float(r['loss'])+CQ*int(r['labels'])+CS*int(r['switches'])
            if abs(expected_net-float(r['net']))>1e-8: errors.append(tag+': net')
            rows.append((path.parent.name,r))
    # Compare recorded harm with paired never-switch economic outcome where available.
    control={}
    for run,r in rows:
        if r['policy']=='CONTROL_never_switch': control[(run,r['regime'],r['ep'],r['seed'])]=float(r['net'])
    harm_checks=0
    for run,r in rows:
        if r['policy']=='CONTROL_never_switch': continue
        key=(run,r['regime'],r['ep'],r['seed'])
        if key in control:
            harm_checks+=1
            if abs((float(r['net'])-control[key])-float(r['harm']))>1e-8: errors.append(f'{run}:{r["regime"]}:{r["ep"]}:{r["seed"]}:{r["policy"]}: harm')
    result={
      'audit':'PASS' if not errors else 'FAIL',
      'run_dirs':[p.parent.name for p in RUNS],
      'rows':len(rows),
      'flag_checks':['ever_promote','n_promotions','first_deploy','per-promotion EI from stored rest_sum and c_s','net cost identity','paired harm vs CONTROL_never_switch where available'],
      'paired_harm_checks':harm_checks,
      'mismatches':len(errors),
      'first_mismatches':errors[:20],
      'limitations':['Run-2 event streams were re-windowed from reused source data, not independent datasets.', 'Checks stored flag arithmetic and cost identities; they do not reproduce policy trajectories from source NPZ files or establish statistical validity.']
    }
    text=json.dumps(result,indent=2)+'\n'
    if a.out:
      out=a.out if a.out.is_absolute() else ROOT/a.out; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(text)
    print(text,end='')
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main()
