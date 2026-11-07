"""Markdown status/summary for Stage-B tranche 2 (A1). Every number is copied from ledger records (suite v2); nothing is
recomputed from memory. Used by the runner after every commit and by ``scripts/d2a_rar/run_stage_b_t2.py --report``."""

from __future__ import annotations

import json
import time
from collections import Counter
from datetime import UTC, datetime

from . import ledger as lg


def _v2_records(ledger_path) -> list[dict]:
    return [r for r in lg.read_all(ledger_path) if r.get("suite") == "v2" and r.get("stage") == "B"]


def _best_target(r: dict) -> dict | None:
    tgt = [
        x
        for x in r["uncertainty"]["dJ_vs_strongest"]
        if x["role"] in ("alternative", "adverse_sampling_stress")
    ]
    return max(tgt, key=lambda x: x["rel_improvement"]) if tgt else None


def _fmt_ci(x: dict) -> str:
    return f"{x['dJ_mean']:+.2f} [{x['dJ_ci95'][0]:+.2f}, {x['dJ_ci95'][1]:+.2f}]"


def _validity(r: dict) -> str:
    v = r["results"]["validity"]["candidate"]
    if not v.get("claimed"):
        return f"no validity claim (null={v.get('null')})"
    return f"{v['metric']} {v['k']}/{v['n']} ({v['rate']:.3f}), CP95 upper {v['cp95_upper']:.3f}, screen-level"


def _vs(r: dict, comp: str) -> list[dict]:
    return [
        x
        for x in r["baseline_relative"]["dJ_vs_each_implemented_comparator"].get(comp, [])
        if x["role"] in ("alternative", "adverse_sampling_stress")
    ]


def _q2_reading(
    recs: list[dict], comps: tuple[str, str] = ("pending_cap", "fixed_schedule")
) -> list[str]:
    """Mandate Q2 stop rule: does any Q2 candidate beat pending_cap AND fixed_schedule on a target cell (paired CI < 0)?"""
    out = []
    q2 = [
        r
        for r in recs
        if r["decision"] in ("KEEP", "DISCARD", "UNVERIFIED") and r.get("seed_group")
    ]
    both, rows = [], []
    for r in q2:
        row = {"id": r["candidate_id"], "method": r["method"], "dec": r["decision"]}
        ok = {}
        for comp in comps:
            xs = _vs(r, comp)
            wins = [x for x in xs if x["dJ_ci95"][1] < 0]
            best = min(xs, key=lambda x: x["dJ_mean"]) if xs else None
            ok[comp] = bool(wins)
            row[comp] = f"{best['id']} {_fmt_ci(best)}" if best else "n/a"
        if ok[comps[0]] and ok[comps[1]]:
            both.append(row)
        rows.append(row)
    out.append(
        f"* Records with a v2 result: {len(q2)}; candidates whose paired CI is entirely below 0 against BOTH "
        f"{comps[0]} and {comps[1]} on at least one target cell: **{len(both)}**."
    )
    if both:
        out += [
            "",
            f"| candidate | method | decision | best target cell vs {comps[0]} (dJ [95% CI]) | vs {comps[1]} |",
            "|---|---|---|---|---|",
        ]
        out += [
            f"| {x['id']} | {x['method']} | {x['dec']} | {x[comps[0]]} | {x[comps[1]]} |"
            for x in both
        ]
    else:
        out.append(
            "* No candidate beats both simple controls on a target cell with a paired CI excluding 0. Best (most negative) dJ per candidate is listed in the full table below."
        )
    return out


def _section(recs: list[dict], title: str, controls: tuple[str, str], stop_title: str) -> list[str]:
    lines = [f"# {title}", ""]
    tally = Counter(r["decision"] for r in recs)
    lines += [
        "## Decision counts",
        "",
        ", ".join(f"{k}={v}" for k, v in sorted(tally.items())) or "none yet",
        "",
    ]
    nk = [r for r in recs if r.get("results", {}).get("near_keep")]
    keeps = [r for r in recs if r["decision"] == "KEEP"]
    lines += [
        "## KEEP and near-KEEP",
        "",
        (
            "KEEP = section 4 satisfied under A1. near-KEEP = DISCARD only through the control-cell / host-ablation / "
            "complexity / simple-control criteria: valid under its claimed null, not invalid-aggressive, and an effect "
            "label other than 'none' on its best target cell against the per-cell strongest applicable comparator. "
            "dJ = J(candidate) - J(comparator), negative = candidate better, 95% paired bootstrap CI."
        ),
        "",
    ]
    if keeps or nk:
        lines += [
            "| decision | candidate | method | best target cell (comparator) | dJ [95% CI] | effect | validity (claimed null) | failed checks |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in keeps + nk:
            b = _best_target(r)
            lines.append(
                f"| {r['decision']} | {r['candidate_id']} | {r['method']} | {b['id']}:{b['family']} ({b['comparator']}) | {_fmt_ci(b)} | "
                f"{r['effect_label_vs_strongest']} (rel {b['rel_improvement']:+.3f}) | {_validity(r)} | "
                f"{'; '.join(x[:90] for x in r['results']['discard_reasons']) or '-'} |"
            )
    else:
        lines.append("None.")
    lines += ["", f"## {stop_title}", ""]
    lines += _q2_reading(recs, controls)
    lines += [
        "",
        "## All records",
        "",
        "| candidate | method | decision | effect | best target cell (comparator) dJ [95% CI] | simple controls beaten? | validity | v1-regression |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in recs:
        if r.get("results") and r.get("uncertainty"):
            b = _best_target(r)
            lines.append(
                f"| {r['candidate_id']} | {r['method']} | {r['decision']}{'/' + r['duplicate_of'] if r.get('duplicate_of') else ''} | "
                f"{r.get('effect_label_vs_strongest', '-')} | {b['id'] + ' (' + b['comparator'] + ') ' + _fmt_ci(b) if b else '-'} | "
                f"{r['results'].get('beats_simple_controls')} | {_validity(r)} | {len(r['results'].get('v1_regressions', []))} |"
            )
        else:
            lines.append(
                f"| {r['candidate_id']} | {r.get('method')} | {r['decision']} | - | {r.get('error', r.get('invalid_reason', ''))[:80]} | - | - | - |"
            )
    lines.append("")
    return lines


def _progress(state: dict | None, label: str) -> list[str]:
    if not state:
        return []
    el = (state.get("updated", time.time()) - state["t0"]) / 60
    return [
        "".join(
            [
                f"* [{label}] phase: {state['phase']}; experiments done this launch: {state['done']} / {state['total']}; elapsed {el:.1f} min; ",
                f"in flight: {', '.join(state['inflight']) or 'none'}; last: {state.get('last', '')}; ",
                f"not run this launch: {json.dumps(state['not_run'], sort_keys=True)}",
            ]
        ),
    ]


def build(
    ledger_path=lg.LEDGER_PATH,
    state: dict | None = None,
    scope: dict | None = None,
    state_iii: dict | None = None,
    scope_iii: dict | None = None,
) -> str:
    allrecs = _v2_records(ledger_path)
    recs_iii = [r for r in allrecs if r.get("scope") == "iii"]
    recs_i = [r for r in allrecs if r.get("scope") != "iii"]
    lines = ["# WP6 Stage B tranche 2 status (Amendment A1; auto-generated)", ""]
    lines.append(f"Updated: {datetime.now(UTC).isoformat(timespec='seconds')}  ")
    lines.append(
        f"Ledger head: `{lg.head(ledger_path)}` ({len(lg.read_all(ledger_path))} records; suite-v2: {len(recs_i)} scope i-ii, {len(recs_iii)} scope iii)  "
    )
    lines.append(f"Branch commit: `{lg.current_git_commit()}`")
    lines.append("")
    if scope:
        lines.append(
            f"Scope (i-ii) file `results/d2a_rar/stage_b/tranche2_scope.json`: {scope['n_selected']} selected (cap {scope['cap']}); "
            f"counts {json.dumps(scope['scope_counts'])}."
        )
    if scope_iii:
        lines.append(
            f"Scope (iii) file `results/d2a_rar/stage_b/tranche2_scope_iii.json`: {scope_iii['n_selected']} Q1 evidence identities; "
            f"cells {', '.join(scope_iii['cells'])}."
        )
    lines += _progress(state, "scope i-ii") + _progress(state_iii, "scope iii")
    lines.append("")
    lines += _section(
        recs_i,
        "Scope (i)-(ii): DUPLICATE-of-host-identical and family-gap identities (Q2) on DEV_SUITE_v2",
        ("pending_cap", "fixed_schedule"),
        "Mandate Q2 stop rule (candidates vs pending_cap / fixed_schedule on target cells)",
    )
    if recs_iii or scope_iii:
        lines += _section(
            recs_iii,
            "Scope (iii): Q1 evidence identities in the evidence promoter shell (v1 Q1 row + compatible v2 cells)",
            ("markov_lr_gate", "thinned_hedged_gate"),
            "Q1 simple-control reading (section 4 item 4: vs Markov-LR and the gap-10 thinned gate, target cells)",
        )
    lines += [
        "Ledger: `docs/d2a_rar/registry/EXPERIMENT_LEDGER.jsonl`; logs: `results/d2a_rar/stage_b/stage_b_t2_run.log`, `stage_b_t2_iii_run.log`.",
        "",
    ]
    return "\n".join(lines)
