#!/usr/bin/env python3
"""Summarize the registered 1,000-seed P4 HMM-null misspecification follow-up."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from .analyze_h2_round5 import wilson
except ImportError:  # direct script execution from this directory
    from analyze_h2_round5 import wilson

ROOT=Path(__file__).resolve().parents[2]
POLICIES=["A5b","P1_renew","P1_union","P1_A5b_c10","D2","rmm:gated_deployment+RMM","P6_LRMD_U"]


def summarize(records:Path)->tuple[dict,str]:
    d=pd.read_json(records,lines=True)
    if set(d.policy.unique())!=set(POLICIES):
        raise ValueError(f"policy coverage mismatch: {sorted(d.policy.unique())}")
    if set(d.regime.unique())!={"P_hmm_null"} or len(d)!=1000*len(POLICIES):
        raise ValueError(f"expected 7,000 rows from 1,000 seeds, got {len(d)}")
    if d.groupby(["seed","policy"]).size().ne(1).any() or set(d.seed.unique())!=set(range(1000)):
        raise ValueError("seed/policy coverage incomplete or duplicated")
    result={"protocol":"post-development P4 HMM-null out-of-class stress follow-up",
            "regime":"P_hmm_null","seed_base":2026110802,"n_seeds":1000,
            "policies":{},"limitations":[
                "The hidden-state HMM is outside A5b's declared first-order stationary Markov null.",
                "Rates describe this fixed generator and do not establish guarantee validity or theorem failure.",
                "P1_renew additionally assumes i.i.d. observation gaps; this run does not establish that assumption."]}
    lines=["# P4 Round-5 HMM-null misspecification follow-up","",
           "1,000 seeds on the registered `P_hmm_null` generator (`hmm_p=(0.3,0.7)`). This is an out-of-class stress test, not a validity test.","",
           "| Policy | Promotions / 1,000 | Rate [Wilson 95%] | Mean J | Mean labels |","|---|---:|---:|---:|---:|"]
    for policy,g in d.groupby("policy"):
        k=int(g.ever_promote.sum());n=len(g)
        row={"promotions":k,"n":n,"rate":k/n,"wilson95":wilson(k,n),
             "mean_net":float(g.net.mean()),"mean_labels":float(g.labels.mean())}
        result["policies"][policy]=row
        lines.append(f"| {policy} | {k}/{n} | {k/n:.3f} [{row['wilson95'][0]:.3f}, {row['wilson95'][1]:.3f}] | {row['mean_net']:.1f} | {row['mean_labels']:.1f} |")
    lines += ["","## Limits","",*[f"- {x}" for x in result["limitations"]],""]
    return result,"\n".join(lines)


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("records",type=Path)
    ap.add_argument("--out",type=Path,default=Path("docs/sprint2/family_p/P4_hmm_round5.json"))
    a=ap.parse_args();j,md=summarize(a.records if a.records.is_absolute() else ROOT/a.records)
    out=a.out if a.out.is_absolute() else ROOT/a.out;out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(j,indent=2)+"\n");out.with_suffix(".md").write_text(md)
    print(f"wrote {out} and {out.with_suffix('.md')}");return 0

if __name__=="__main__":raise SystemExit(main())
