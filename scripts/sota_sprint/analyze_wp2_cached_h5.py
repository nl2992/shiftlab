"""Historical cached-real sensitivity for WP2 H5, clustered by source dataset."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

METRICS = {"net": "net", "delay": "delay_t", "labels": "labels", "promotion": "ever_promote"}
PAIRS = [("A5b", "QSG"), ("D5", "D2")]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--records', default='outputs/sprint2/WP2/cached_real_h5/records.jsonl')
    ap.add_argument('--csv', default='outputs/sprint2/WP2/cached_real_h5_h5_paired.csv')
    ap.add_argument('--json', default='docs/sprint2/wp2/cached_real_h5_summary.json')
    ap.add_argument('--boot', type=int, default=10000)
    a=ap.parse_args()
    df=pd.read_json(a.records, lines=True)
    df['delay_t']=np.where(df.first_deploy>=0,df.first_deploy,df["T"]).astype(float)
    # Match by source, episode, and seed before filtering or averaging.
    out={"records":len(df),"seed_base":2026110901,"scope":"historical cached real; development-exposed; descriptive only",
         "filter":"episodes with mean realized advantage ep_adv > 0 across seeds (retrospective selection)","pairs":{}}
    allrows=[]
    rng=np.random.default_rng(2026110901)
    for left,right in PAIRS:
        x=df[df.policy==left].set_index(['regime','ep','seed'])
        y=df[df.policy==right].set_index(['regime','ep','seed'])
        z=x[list(METRICS.values())].join(y[list(METRICS.values())],lsuffix='_l',rsuffix='_r',how='inner')
        # Ep advantage is common to policies; retain only realized-positive episodes as in H5.
        adv=df.groupby(['regime','ep']).ep_adv.mean()
        z=z.reset_index()
        z=z[z.set_index(['regime','ep']).index.isin(adv[adv>0].index)]
        for metric,col in METRICS.items(): z[metric]=z[f'{col}_l']-z[f'{col}_r']
        # First average seeds within episode, then episodes within dataset/source.
        ep=z.groupby(['regime','ep'],as_index=False)[list(METRICS)].mean()
        ds=ep.groupby('regime')[list(METRICS)].mean()
        n_ep=ep.groupby('regime').size().to_dict()
        vals=ds.to_numpy(float); n=len(vals)
        idx=rng.integers(0,n,(a.boot,n)) if n else np.empty((0,0),int)
        boot=vals[idx].mean(1) if n else np.empty((0,len(METRICS)))
        summary={"n_sources":n,"n_positive_episodes":int(len(ep)),"by_source":{},"mean_delta":{},"ci95_source_cluster":{}}
        for source,row in ds.iterrows():
            summary['by_source'][source]={"positive_episodes":int(n_ep[source]),**{k:float(row[k]) for k in METRICS}}
        for j,k in enumerate(METRICS):
            summary['mean_delta'][k]=float(vals[:,j].mean()) if n else None
            summary['ci95_source_cluster'][k]=[float(v) for v in np.quantile(boot[:,j],[.025,.975])] if n else [None,None]
        out['pairs'][f'{left}-{right}']=summary
        for _,row in ep.iterrows(): allrows.append({"pair":f'{left}-{right}',**row.to_dict()})
    Path(a.csv).parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(allrows).to_csv(a.csv,index=False)
    Path(a.json).parent.mkdir(parents=True,exist_ok=True)
    Path(a.json).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
