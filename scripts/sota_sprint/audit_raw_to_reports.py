#!/usr/bin/env python3
"""Recompute key derived Sprint 2 reports from frozen run records and compare them.

The audit covers strict comparator-pool sensitivities for validation/WP1/WP2, the corrected Family-H
real replay, WP1/WP2 tables and diagnostics, P6 and R5 real-stream summaries, H/T development summaries, selected R Track-E/V cells, P1/P2
checks, H/R/T/P Track-R tables, and the T3 matched-host Track-R follow-up. Broader P-family development tables are checked by
audit_p_family_development.py; free-text candidate claims remain outside these numerical audits.
"""
from __future__ import annotations
import argparse, glob, json, math, subprocess, sys, tempfile
import re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]

def run(args: list[str]) -> None:
    # Use the pinned project environment; system Python may not have the research dependencies.
    p=subprocess.run(['uv','run','python',*args],cwd=ROOT,text=True,capture_output=True)
    if p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}")

def dirs(pattern: str) -> list[str]:
    return sorted(glob.glob(str(ROOT/pattern)))

def compare_json(a: Path,b: Path)->list[str]:
    x=json.loads(a.read_text());y=json.loads(b.read_text());dif=[]
    def walk(u: Any,v: Any,path: str)->None:
        if type(u)!=type(v): dif.append(f"{path}: type {type(u).__name__} != {type(v).__name__}");return
        if isinstance(u,dict):
            if set(u)!=set(v):dif.append(f"{path}: keys differ (missing={sorted(set(u)-set(v))[:5]}, extra={sorted(set(v)-set(u))[:5]})")
            for k in sorted(set(u)&set(v)):walk(u[k],v[k],f"{path}.{k}")
        elif isinstance(u,list):
            if len(u)!=len(v):dif.append(f"{path}: list lengths {len(u)} != {len(v)}")
            for i,(uu,vv) in enumerate(zip(u,vv_list(v))):walk(uu,vv,f"{path}[{i}]")
        elif isinstance(u,(int,float)) and not isinstance(u,bool):
            if math.isnan(float(u)) and math.isnan(float(v)): return
            if not math.isclose(float(u),float(v),rel_tol=1e-12,abs_tol=1e-12):dif.append(f"{path}: {u!r} != {v!r}")
        elif u!=v:dif.append(f"{path}: {u!r} != {v!r}")
    def vv_list(v):return v
    walk(x,y,"$")
    return dif

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=Path('docs/sprint2/raw_report_audit.json'));a=ap.parse_args()
    checks=[]
    def add(name:str,generated:Path,committed:Path,kind='json'):
        if not generated.exists() or not committed.exists():
            checks.append({'name':name,'status':'FAIL','reason':'missing generated or committed file','generated_exists':generated.exists(),'committed_exists':committed.exists()});return
        diffs=compare_json(generated,committed) if kind=='json' else ([] if generated.read_bytes()==committed.read_bytes() else ['byte content differs'])
        checks.append({'name':name,'status':'PASS' if not diffs else 'FAIL','generated':str(generated),'committed':str(committed),'differences':diffs[:20],'difference_count':len(diffs)})
    with tempfile.TemporaryDirectory(prefix='shiftlab_raw_audit_') as td:
        t=Path(td)
        run(['scripts/sota_sprint/analyze_validation.py','--amendment-dir',str(t/'validation')])
        add('amended validation JSON',t/'validation/validation_results.json',ROOT/'docs/sprint2/validation_amendment_20261104/validation_results.json')
        add('amended validation Markdown',t/'validation/validation_results.md',ROOT/'docs/sprint2/validation_amendment_20261104/validation_results.md','text')
        run(['scripts/sota_sprint/analyze_validation.py','--strict-published-dir',str(t/'validation_strict_published')])
        add('strict published-pool validation JSON',t/'validation_strict_published/validation_results.json',ROOT/'docs/sprint2/validation_strict_published_20261104/validation_results.json')
        add('strict published-pool validation Markdown',t/'validation_strict_published/validation_results.md',ROOT/'docs/sprint2/validation_strict_published_20261104/validation_results.md','text')
        h_corrected_relative='outputs/sprint2/round5/H_corrected_real_20/records.jsonl'
        h_corrected_raw=ROOT/h_corrected_relative
        if h_corrected_raw.exists():
            run(['scripts/sota_sprint/analyze_h_corrected_real.py',h_corrected_relative,
                 '--json',str(t/'H_corrected_real_20.json'),'--markdown',str(t/'H_corrected_real_20.md')])
            add('H corrected 20-seed real JSON',t/'H_corrected_real_20.json',ROOT/'docs/sprint2/family_h/corrected_real_20.json')
            add('H corrected 20-seed real Markdown',t/'H_corrected_real_20.md',ROOT/'docs/sprint2/family_h/corrected_real_20.md','text')
        else:
            checks.append({'name':'H corrected 20-seed real analysis','status':'FAIL',
                           'reason':f'missing raw records: {h_corrected_raw}'})
        run(['scripts/sota_sprint/late_real.py','report','--primary','outputs/sprint2/WP1/primary',
             '--twin','outputs/sprint2/WP1/twin','--sens',*dirs('outputs/sprint2/WP1/sens_*'),
             '--supplemental','outputs/sprint2/WP1/strict_extra_discern_design_floor',
             '--classes','outputs/sprint2/WP1/classes.json','--strict-published-subset',
             '--out',str(t/'wp1_strict_published_subset.json')])
        add('WP1 complete strict published-pool JSON',t/'wp1_strict_published_subset.json',
            ROOT/'docs/sprint2/wp1/strict_published_subset_20261104.json')
        wp1=['scripts/sota_sprint/late_real.py','report','--primary','outputs/sprint2/WP1/primary','--twin','outputs/sprint2/WP1/twin','--sens',*dirs('outputs/sprint2/WP1/sens_*'),'--classes','outputs/sprint2/WP1/classes.json','--amended-no-xu','--out',str(t/'wp1.json')]
        run(wp1);add('amended WP1 JSON',t/'wp1.json',ROOT/'docs/sprint2/wp1/results_amended_no_xu.json')
        run(['scripts/sota_sprint/wp2_analyze.py','--amendment-dir',str(t/'wp2')])
        add('amended WP2 JSON',t/'wp2/results.json',ROOT/'docs/sprint2/wp2/amended_no_xu/results.json')
        add('amended WP2 tables',t/'wp2/tables.md',ROOT/'docs/sprint2/wp2/amended_no_xu/tables.md','text')
        run(['scripts/sota_sprint/wp2_analyze.py','--amendment-dir',str(t/'wp2_no_xu_pool'),'--exclude-xu-pool'])
        add('WP2 no-Xu pooled sensitivity JSON',t/'wp2_no_xu_pool/results.json',ROOT/'docs/sprint2/wp2/amended_no_xu_pool/results.json')
        add('WP2 no-Xu pooled sensitivity tables',t/'wp2_no_xu_pool/tables.md',ROOT/'docs/sprint2/wp2/amended_no_xu_pool/tables.md','text')
        run(['scripts/sota_sprint/wp2_analyze.py','--strict-published-dir',str(t/'wp2_strict_published')])
        add('WP2 strict published-pool JSON',t/'wp2_strict_published/results.json',ROOT/'docs/sprint2/wp2/strict_published_20261104/results.json')
        add('WP2 strict published-pool tables',t/'wp2_strict_published/tables.md',ROOT/'docs/sprint2/wp2/strict_published_20261104/tables.md','text')
        run(['scripts/sota_sprint/wp1_false_rollback.py','--workers','4','--out',str(t/'wp1_false_rollback.json')])
        add('WP1 false-rollback trace audit',t/'wp1_false_rollback.json',ROOT/'docs/sprint2/wp1/false_rollback_audit.json')
        run(['scripts/sota_sprint/wp1_giacomini_rossi.py','--alpha','0.05','--out',str(t/'wp1_gr.json')])
        add('WP1 Giacomini-Rossi JSON',t/'wp1_gr.json',ROOT/'docs/sprint2/wp1/gr_one_time_reversal.json')
        add('WP1 Giacomini-Rossi Markdown',t/'wp1_gr.md',ROOT/'docs/sprint2/wp1/gr_one_time_reversal.md','text')
        run(['scripts/sota_sprint/analyze_wp1_clock_ablation.py',
             'outputs/sprint2/WP1/clock_ablation_posthoc3/records.jsonl','--out',str(t/'wp1_clock.json')])
        add('WP1 label/timestamp-clock ablation JSON',t/'wp1_clock.json',ROOT/'docs/sprint2/wp1/clock_ablation_posthoc3.json')
        add('WP1 label/timestamp-clock ablation Markdown',t/'wp1_clock.md',ROOT/'docs/sprint2/wp1/clock_ablation_posthoc3.md','text')
        run(['scripts/sota_sprint/analyze_h2_round5.py',
             '--synthetic','outputs/sprint2/round5/H2_followup100/records.jsonl',
             '--null','outputs/sprint2/round5/H2_markov_null1000/records.jsonl',
             '--real','outputs/sprint2/round5/H2_real14_3seed/records.jsonl',
             '--out',str(t/'H2_round5.json')])
        add('H2 Round-5 follow-up JSON',t/'H2_round5.json',ROOT/'docs/sprint2/family_h/round5_h2.json')
        add('H2 Round-5 follow-up Markdown',t/'H2_round5.md',ROOT/'docs/sprint2/family_h/round5_h2.md','text')
        run(['scripts/sota_sprint/analyze_p4_hmm_followup.py',
             'outputs/sprint2/round5/P4_hmm_null1000/records.jsonl','--out',str(t/'P4_hmm.json')])
        add('P4 HMM Round-5 JSON',t/'P4_hmm.json',ROOT/'docs/sprint2/family_p/P4_hmm_round5.json')
        add('P4 HMM Round-5 Markdown',t/'P4_hmm.md',ROOT/'docs/sprint2/family_p/P4_hmm_round5.md','text')
        run(['scripts/sota_sprint/analyze_wp1_erb_postdev.py','outputs/sprint2/round5/wp1_erb_reversal_postdev100','--out',str(t/'wp1_erb.json')])
        add('WP1 E_rb follow-up JSON',t/'wp1_erb.json',ROOT/'docs/sprint2/wp1/erb_reversal_postdev100.json')
        run(['scripts/sota_sprint/analyze_p6_twin_bike.py','outputs/sprint2/round5/p6_twin_bike_1000','--out',str(t/'p6_twin.json')])
        add('P6 twin-bike JSON',t/'p6_twin.json',ROOT/'docs/sprint2/family_p/p6_twin_bike_1000.json')
        run(['scripts/sota_sprint/analyze_p6_selection_adjusted.py','outputs/sprint2/round5/P6_corrected_comparators_100/records.jsonl','--out',str(t/'p6_selection.json')])
        add('P6 selection-adjusted sensitivity JSON',t/'p6_selection.json',ROOT/'docs/sprint2/family_p/P6_selection_adjusted.json')
        r5_real=ROOT/'outputs/sprint2/round5/R5_all14_real20'
        if (r5_real/'manifest.json').exists() and (r5_real/'records.jsonl').exists():
            run(['scripts/sota_sprint/analyze_r5_all14_real.py','--input','outputs/sprint2/round5/R5_all14_real20',
                 '--json',str(t/'R5_all14_real.json'),'--markdown',str(t/'R5_all14_real.md')])
            add('R5 all-14-source real replay JSON',t/'R5_all14_real.json',
                ROOT/'docs/sprint2/family_r/R5_all14_real_results.json')
            add('R5 all-14-source real replay Markdown',t/'R5_all14_real.md',
                ROOT/'docs/sprint2/family_r/R5_all14_real_results.md','text')
        else:
            checks.append({'name':'R5 all-14-source real replay','status':'FAIL',
                           'reason':f'missing raw run artifacts under {r5_real.relative_to(ROOT)}'})
        # Development summaries with saved, deterministic summary-generation entry points.
        run(['scripts/sota_sprint/fam_h.py','summarize','--dirs',
             'outputs/sprint2/H/screen1,outputs/sprint2/H/screen1c,outputs/sprint2/H/screen1b',
             '--out',str(t/'H_dev.json'),'--legacy-comparator-pool'])
        add('H development screen JSON',t/'H_dev.json',ROOT/'outputs/sprint2/H/sum_screen1_all.json')
        run(['scripts/sota_sprint/fam_t.py','outputs/sprint2/T/devA','outputs/sprint2/T/devB',
             '--out',str(t/'T_dev.json')])
        add('T development screen JSON',t/'T_dev.json',ROOT/'outputs/sprint2/T/dev_summary.json')
        add('T development screen Markdown',t/'T_dev.md',ROOT/'outputs/sprint2/T/dev_summary.md','text')
        # Family R's saved Track-E/V report is a compact hand-built projection of these columns.
        # Recompute every reported dev/eval policy cell from the frozen records.
        import pandas as pd  # noqa: PLC0415
        from bench2 import RISK_ALTS  # noqa: PLC0415
        rdev=pd.read_json(ROOT/'outputs/sprint2/R/dev_screen_a05/records.jsonl',lines=True)
        reval=pd.read_json(ROOT/'outputs/sprint2/R/trackR/eval_a0.05/records.jsonl',lines=True)
        rderived={}
        for label,frame in [('dev',rdev),('eval',reval)]:
            out={}
            for policy,g in frame.groupby('policy'):
                reg={name: q for name,q in g.groupby('regime')}
                required={'F0_null','F0_worse','F5_dep_null_r8','F5_dep_null_r95','F3_reversal_800','F5_dep_better_r8'}
                if not required.issubset(reg):
                    continue
                alt=g[g.regime.isin(RISK_ALTS)]
                out[policy]={'iid':round(float(pd.concat([reg['F0_null'],reg['F0_worse']]).ever_promote.mean()),3),
                    'r8':round(float(reg['F5_dep_null_r8'].ever_promote.mean()),3),
                    'r95':round(float(reg['F5_dep_null_r95'].ever_promote.mean()),3),
                    'alt':round(float(alt.net.mean()),3),
                    'rev':round(float(reg['F3_reversal_800'].net.mean()),3),
                    'dep8':round(float(reg['F5_dep_better_r8'].net.mean()),3),
                    'lab':round(float(alt.labels.mean()),3)}
            rderived[label]=out
        stored=json.loads((ROOT/'outputs/sprint2/R/analysis/trackE_V_a05.json').read_text())
        rcheck={k:stored[k] for k in ('dev','eval')}
        # Stored report values are rounded to 3 decimals; compare only those complete cells.
        comparable={k:{p:{m:v for m,v in row.items() if m in ('iid','r8','r95','alt','rev','dep8','lab')}
                       for p,row in pols.items()} for k,pols in rderived.items()}
        (t/'R_trackEV_derived.json').write_text(json.dumps(comparable,indent=1)+'\n')
        # Use exact structural/value comparison after matching the report's rounding convention.
        rstored={k:{p:{m:round(float(v),3) for m,v in row.items() if m in ('iid','r8','r95','alt','rev','dep8','lab')}
                    for p,row in pols.items()} for k,pols in rcheck.items()}
        diffs=[]
        for part in ('dev','eval'):
            if set(comparable[part])!=set(rstored[part]):
                diffs.append(f'{part}: policy IDs differ')
            for policy in set(comparable[part])&set(rstored[part]):
                for metric in set(comparable[part][policy])|set(rstored[part][policy]):
                    if abs(comparable[part][policy].get(metric,0)-rstored[part][policy].get(metric,0))>0.00101:
                        diffs.append(f'{part}.{policy}.{metric}: {comparable[part][policy].get(metric)} != {rstored[part][policy].get(metric)}')
        checks.append({'name':'R Track E/V dev/eval numeric cells','status':'PASS' if not diffs else 'FAIL',
                       'generated':'outputs/sprint2/R/dev_screen_a05/records.jsonl + outputs/sprint2/R/trackR/eval_a0.05/records.jsonl',
                       'committed':'outputs/sprint2/R/analysis/trackE_V_a05.json','differences':diffs[:20],
                       'difference_count':len(diffs),'cell_count':sum(len(v)*7 for v in comparable.values())})
        # P1 diagnostic: deterministic evaluator-side calculation, including its Monte Carlo seed.
        run(['scripts/sota_sprint/fam_p.py','p1diag','--reps','100','--out',str(t/'P1_diag.json')])
        add('P1 power diagnostic JSON',t/'P1_diag.json',ROOT/'outputs/sprint2/P/p1diag/p1diag.json')
        # P2 conditional/marginal error table: episode-level definition, not promotion-level rate.
        p2=json.loads((ROOT/'outputs/sprint2/P/p2p3/p2p3.json').read_text())
        p2_policies=['A5b','gated_adaptive_range+front','rmm:gated_deployment+RMM','D2','QSG','P3_follow']
        episodes=[r for r in p2['synthetic'] if r['p']<=0.5]
        p2_derived={}
        for policy in p2_policies:
            rows=[r for r in episodes if r['policy']==policy]
            v2=sum(bool(r['promotions']) for r in rows)/len(rows)
            v1=sum(any(float(pr['Cpol500'])<=0 for pr in r['promotions']) for r in rows)/len(rows)
            p2_derived[policy]={'V2':round(v2,3),'V1':round(v1,3)}
        p2_text=(ROOT/'docs/sprint2/family_p/P2P3_objectives_harm.md').read_text()
        table=p2_text.split('| policy | V2 | V1 |',1)[1].split('\n\n',1)[0]
        p2_saved={}
        for row in re.findall(r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$',table,re.M):
            name,v2,v1=row
            try:
                display_name=name.strip()
                policy_id={'RMM (gated)':'rmm:gated_deployment+RMM'}.get(display_name,display_name)
                p2_saved[policy_id]={'V2':round(float(v2.strip()),3),'V1':round(float(v1.strip()),3)}
            except ValueError:  # Markdown separator row
                continue
        p2diff=[]
        if p2_derived!=p2_saved:p2diff=[f'{k}: computed={p2_derived.get(k)}; report={p2_saved.get(k)}' for k in p2_policies if p2_derived.get(k)!=p2_saved.get(k)]
        checks.append({'name':'P2 episode-level V1/V2 error table','status':'PASS' if not p2diff else 'FAIL',
                       'generated':'outputs/sprint2/P/p2p3/p2p3.json','committed':'docs/sprint2/family_p/P2P3_objectives_harm.md',
                       'differences':p2diff,'difference_count':len(p2diff),'cell_count':2*len(p2_policies),
                       'definition':'Per-episode any-promotion V2; per-episode any promotion with Cpol500<=0 V1, among p<=.5 episodes.'})
        risk_specs=[
          ('H Track R',['outputs/sprint2/H/trackR/b2026110701_a*'],['outputs/sprint2/H/trackR/b2026110711_a*'],ROOT/'docs/sprint2/family_h/track_R.json',ROOT/'docs/sprint2/family_h/track_R.md'),
          ('R Track R',['outputs/sprint2/R/dev_screen_a05','outputs/sprint2/R/trackR/dev_a*','outputs/sprint2/R/trackR_H/dev_a*'],['outputs/sprint2/R/trackR/eval_a*','outputs/sprint2/R/trackR_H/eval_a*'],ROOT/'outputs/sprint2/R/analysis/risk_curves.json',ROOT/'outputs/sprint2/R/analysis/risk_curves.md'),
          ('T Track R',['outputs/sprint2/T/devA','outputs/sprint2/T/devB','outputs/sprint2/T/R_dev_a*'],['outputs/sprint2/T/R_eval_a*'],ROOT/'outputs/sprint2/T/trackR.json',ROOT/'outputs/sprint2/T/trackR.md'),
          ('P Track R',['outputs/sprint2/P/trackR/b2026110701_a*','outputs/sprint2/P/trackR2/b2026110701_a*'],['outputs/sprint2/P/trackR/b2026110711_a*','outputs/sprint2/P/trackR2/b2026110711_a*'],ROOT/'docs/sprint2/family_p/trackR.json',ROOT/'docs/sprint2/family_p/trackR.md'),
        ]
        for name,devp,evp,jdest,mdest in risk_specs:
            dev=[d for pat in devp for d in dirs(pat)];ev=[d for pat in evp for d in dirs(pat)]
            run(['scripts/sota_sprint/risk_curves.py','--dev',*dev,'--eval',*ev,'--out',str(t/f'{name[0]}_risk.json')])
            jgen=t/f'{name[0]}_risk.json';mdgen=jgen.with_suffix('.md')
            add(name+' JSON',jgen,jdest)
            if mdest.exists():add(name+' Markdown',mdgen,mdest,'text')
        t3_dev=dirs('outputs/sprint2/T/T3_trackR/dev_a*')
        t3_eval=dirs('outputs/sprint2/T/T3_trackR/eval_a*')
        if len(t3_dev)!=8 or len(t3_eval)!=8:
            checks.append({'name':'T3 matched-host Track-R follow-up','status':'FAIL',
                           'reason':f'expected 8 dev and 8 eval alpha runs; found {len(t3_dev)} and {len(t3_eval)}'})
        else:
            run(['scripts/sota_sprint/risk_curves.py','--dev',*t3_dev,'--eval',*t3_eval,
                 '--out',str(t/'T3_trackR_followup.json')])
            add('T3 matched-host Track-R follow-up JSON',t/'T3_trackR_followup.json',
                ROOT/'docs/sprint2/family_t/T3_trackR_followup.json')
            add('T3 matched-host Track-R follow-up Markdown',t/'T3_trackR_followup.md',
                ROOT/'docs/sprint2/family_t/T3_trackR_followup.md','text')
        t125_dev=dirs('outputs/sprint2/T/T125_trackR/dev_a*')
        t125_eval=dirs('outputs/sprint2/T/T125_trackR/eval_a*')
        if len(t125_dev)!=8 or len(t125_eval)!=8:
            checks.append({'name':'T1/T2/T5 held-out Track-R follow-up','status':'FAIL',
                           'reason':f'expected 8 dev and 8 eval alpha runs; found {len(t125_dev)} and {len(t125_eval)}'})
        else:
            run(['scripts/sota_sprint/risk_curves.py','--dev',*t125_dev,'--eval',*t125_eval,
                 '--out',str(t/'T125_trackR_followup.json')])
            add('T1/T2/T5 held-out Track-R follow-up JSON',t/'T125_trackR_followup.json',
                ROOT/'docs/sprint2/family_t/T1_T2_T5_trackR_followup.json')
            add('T1/T2/T5 held-out Track-R follow-up Markdown',t/'T125_trackR_followup.md',
                ROOT/'docs/sprint2/family_t/T1_T2_T5_trackR_followup.md','text')
        h_dev=dirs('outputs/sprint2/H/trackR_remaining/dev_a*')
        h_eval=dirs('outputs/sprint2/H/trackR_remaining/eval_a*')
        if len(h_dev)!=8 or len(h_eval)!=8:
            checks.append({'name':'H1/H3 Track-R completion JSON','status':'FAIL',
                           'reason':f'expected 8 dev and 8 eval alpha runs; found {len(h_dev)} and {len(h_eval)}'})
        else:
            run(['scripts/sota_sprint/risk_curves.py','--dev',*h_dev,'--eval',*h_eval,
                 '--out',str(t/'H_remaining_risk.json')])
            add('H1/H3 Track-R completion JSON',t/'H_remaining_risk.json',
                ROOT/'docs/sprint2/family_h/track_R_remaining.json')
            add('H1/H3 Track-R completion Markdown',t/'H_remaining_risk.md',
                ROOT/'docs/sprint2/family_h/track_R_remaining.md','text')
            h_rb_dev=dirs('outputs/sprint2/H/trackR_rollback/dev_a*')
            h_rb_eval=dirs('outputs/sprint2/H/trackR_rollback/eval_a*')
            if len(h_rb_dev)!=8 or len(h_rb_eval)!=8:
                checks.append({'name':'H5/H6 Track-R completion JSON','status':'FAIL',
                               'reason':f'expected 8 dev and 8 eval alpha runs; found {len(h_rb_dev)} and {len(h_rb_eval)}'})
            else:
                run(['scripts/sota_sprint/risk_curves.py','--dev',*h_rb_dev,'--eval',*h_rb_eval,
                     '--out',str(t/'H_rollback_risk.json')])
                add('H5/H6 Track-R completion JSON',t/'H_rollback_risk.json',
                    ROOT/'docs/sprint2/family_h/track_R_rollback.json')
                add('H5/H6 Track-R completion Markdown',t/'H_rollback_risk.md',
                    ROOT/'docs/sprint2/family_h/track_R_rollback.md','text')
                run(['scripts/sota_sprint/merge_h_trackr.py','--existing',
                     str(ROOT/'docs/sprint2/family_h/track_R.json'),'--added',
                     str(t/'H_remaining_risk.json'),'--rollback',str(t/'H_rollback_risk.json'),
                     '--out',str(t/'H_all_risk.json')])
                add('Merged Family-H Track-R JSON',t/'H_all_risk.json',
                    ROOT/'docs/sprint2/family_h/track_R_all.json')
                add('Merged Family-H Track-R Markdown',t/'H_all_risk.md',
                    ROOT/'docs/sprint2/family_h/track_R_all.md','text')
        esw_dev=dirs('outputs/sprint2/WP1/trackR_E_swcert_dev_a*')
        esw_eval=dirs('outputs/sprint2/WP1/trackR_E_swcert_eval_a*')
        if len(esw_dev)!=8 or len(esw_eval)!=8:
            checks.append({'name':'WP1 E_swcert Track R JSON','status':'FAIL',
                           'reason':f'expected 8 dev and 8 eval alpha runs; found {len(esw_dev)} and {len(esw_eval)}'})
        else:
            run(['scripts/sota_sprint/risk_curves.py','--dev',*esw_dev,'--eval',*esw_eval,'--out',str(t/'WP1_E_swcert_risk.json')])
            add('WP1 E_swcert Track R JSON',t/'WP1_E_swcert_risk.json',ROOT/'docs/sprint2/wp1/trackR_E_swcert.json')
            add('WP1 E_swcert Track R Markdown',t/'WP1_E_swcert_risk.md',ROOT/'docs/sprint2/wp1/trackR_E_swcert.md','text')
    for check in checks:
        for key in ('generated','committed'):
            value=check.get(key)
            if not isinstance(value,str):
                continue
            candidate=Path(value)
            try:
                check[key]=str(candidate.relative_to(t)) if key=='generated' and candidate.is_relative_to(t) else value
                if key=='generated' and candidate.is_relative_to(t):
                    check[key]='<temporary>/' + check[key]
                elif candidate.is_relative_to(ROOT):
                    check[key]=candidate.relative_to(ROOT).as_posix()
            except ValueError:
                pass
    result={'audit':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':checks,'scope_limitations':['This re-executes derived corrected analyses, strict comparator-pool sensitivities for validation/WP1/WP2, the corrected Family-H replay report, H/T development summaries, P6 and R5 real-stream summaries, selected R Track-E/V cells, P1/P2 checks, H/R/T/P Track-R reports, and the T3 and T1/T2/T5 held-out Track-R follow-ups from saved raw records.', 'It does not reconcile every numeric claim in the P-family development summaries or every narrative claim in the 24-candidate registry.', 'It does not test theorem assumptions, data provenance beyond recorded manifests, or independent validity.']}
    out=a.out if a.out.is_absolute() else ROOT/a.out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['audit']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
