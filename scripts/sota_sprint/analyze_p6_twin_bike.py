"""Summarize P6 twin-bike Monte Carlo with split-level clustering."""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

POLICIES=["P6_LRMD_U","M_LRMD_SUI","A5b","CONTROL_never_switch"]

def ci_cluster(values, nboot=10000, seed=2026110813):
    x=np.asarray(values,float); rng=np.random.default_rng(seed)
    ix=rng.integers(0,len(x),size=(nboot,len(x)))
    means=x[ix].mean(axis=1)
    return [float(np.quantile(means,.025)),float(np.quantile(means,.975))]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('run_dir',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    d=pd.read_json(a.run_dir/'records.jsonl',lines=True)
    with np.load('data/sprint_twin_losses/twin_bike_hour.npz') as cache:
        ep_to_split=np.asarray(cache['split'])
    d['split_cluster']=ep_to_split[d.ep.to_numpy(dtype=int)]
    split_rates=d.groupby(['split_cluster','policy']).ever_promote.mean().unstack()
    split_cost=d.groupby(['split_cluster','policy']).net.mean().unstack()
    res={"status":"POST_DEVELOPMENT_MONTE_CARLO_ON_REUSED_SPLITS","run_dir":str(a.run_dir),"n_split_clusters":int(d.split_cluster.nunique()),"source_datasets":1,"episodes":int(d.ep.nunique()),"seeds_per_episode":int(d.seed.nunique()),"policies":{}}
    for pol in POLICIES:
        x=split_rates[pol].values
        res['policies'][pol]={"mean_promotion_rate":float(x.mean()),"split_cluster_bootstrap_95ci":ci_cluster(x),"splits_above_0_0936":int((x>.0936).sum())}
    contrasts={}
    for pol in ["P6_LRMD_U","A5b"]:
        vals=(split_cost[pol]-split_cost['M_LRMD_SUI']).values
        contrasts[f"{pol}-M_LRMD_SUI"]={"mean_delta_J":float(vals.mean()),"split_cluster_bootstrap_95ci":ci_cluster(vals,seed=2026110814)}
    res['paired_mean_cost_contrasts']=contrasts
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(res,indent=2)+'\n'); print(json.dumps(res,indent=2))
if __name__=='__main__': main()
