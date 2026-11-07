"""Paired CAMS-MAX vs CAMS comparison on matched validation panels."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

PANELS = {
    "synthetic_100": ("outputs/sprint2/CAMS_MAX/validation_synth100", "outputs/sota_sprint/validation/synth", "seed"),
    "null_1000": ("outputs/sprint2/CAMS_MAX/validation_null1000", "outputs/sprint2/CAMS_MAX/validation_null1000_cams", "seed"),
    "out_of_class_1000": ("outputs/sprint2/CAMS_MAX/validation_ooc1000", "outputs/sprint2/CAMS_MAX/validation_ooc1000_cams", "seed"),
    "cached_real_10": ("outputs/sprint2/CAMS_MAX/validation_real_exposed10", "outputs/sota_sprint/validation/real_exposed", "source_cluster"),
    "fresh_real_20": ("outputs/sprint2/CAMS_MAX/validation_real_fresh20", "outputs/sota_sprint/validation/real_fresh", "source_cluster"),
}
METRICS = {"net": "net", "promotion": "ever_promote", "labels": "labels", "deploy_delay": "deploy_delay"}

def load(path):
    d=pd.read_json(path, lines=True)
    # All compared validation panels use T=2000; screen records encode no-promotion as -1.
    d['deploy_delay']=np.where(d.first_deploy>=0,d.first_deploy,2000).astype(float)
    return d

def boot(values, rng, n=10000):
    a=np.asarray(values,float);k=len(a)
    if not k:return [None,None]
    ix=rng.integers(0,k,(n,k)); b=a[ix].mean(axis=1)
    return [float(x) for x in np.quantile(b,[.025,.975])]

def summarize_panel(name, new_path, ref_path, unit, nboot, seed):
    new=load(Path(new_path)/'records.jsonl');ref=load(Path(ref_path)/'records.jsonl')
    new=new[new.policy=='cams_max_adapter'].set_index(['regime','ep','seed'])
    ref=ref[ref.policy=='cams_adapter'].set_index(['regime','ep','seed'])
    common=new.index.intersection(ref.index)
    z=new.loc[common,list(METRICS.values())].join(ref.loc[common,list(METRICS.values())],lsuffix='_new',rsuffix='_ref')
    for metric,col in METRICS.items():z[metric]=z[f'{col}_new']-z[f'{col}_ref']
    z=z.reset_index()
    rng=np.random.default_rng(seed)
    if unit=='seed':
        rows={}
        for regime,g in z.groupby('regime'):
            rows[regime]={"n":int(len(g)),"delta":{},"cams_max":{},"cams":{}}
            for m,col in METRICS.items():
                vals=g[m].to_numpy(float);rows[regime]['delta'][m]={"mean":float(vals.mean()),"ci95":boot(vals,rng,nboot)}
                rows[regime]['cams_max'][m]=float(g[f'{col}_new'].mean())
                rows[regime]['cams'][m]=float(g[f'{col}_ref'].mean())
        return {"panel":name,"unit":"independent seed","matched_rows":int(len(z)),"by_regime":rows}
    # Real streams: average within each episode over seeds, then within source; bootstrap source clusters.
    ep=z.groupby(['regime','ep'],as_index=False)[list(METRICS)].mean()
    src=ep.groupby('regime')[list(METRICS)].mean()
    res={"panel":name,"unit":"source dataset cluster","matched_rows":int(len(z)),
         "episodes":int(len(ep)),"sources":int(len(src)),"by_source":{},"equal_source_mean_delta":{},"source_cluster_ci95":{}}
    for source,row in src.iterrows():res['by_source'][source]={m:float(row[m]) for m in METRICS}
    for m in METRICS:
        vals=src[m].to_numpy(float);res['equal_source_mean_delta'][m]=float(vals.mean());res['source_cluster_ci95'][m]=boot(vals,rng,nboot)
    return res

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='docs/sprint2/CAMS_MAX_VALIDATION.json');ap.add_argument('--boot',type=int,default=10000)
    a=ap.parse_args();out={"scope":"post hoc paired baseline comparison; native CAMS/CAMS-MAX algorithm cores under constant-policy advice with common deployment adapters","panels":{}}
    for i,(name,(new,ref,unit)) in enumerate(PANELS.items()):
        if not (Path(new)/'records.jsonl').exists():raise SystemExit(f'missing CAMS-MAX run: {new}')
        out['panels'][name]=summarize_panel(name,new,ref,unit,a.boot,2026110600+i)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
