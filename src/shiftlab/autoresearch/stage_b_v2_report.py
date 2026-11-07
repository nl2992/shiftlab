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
        xs0, xs1 = _vs(r, comps[0]), _vs(r, comps[1])
        # a target cell where the paired CI is entirely below 0 against BOTH controls simultaneously
        common = [
            (a, b)
            for a, b in zip(xs0, xs1, strict=True)
            if a["id"] == b["id"] and a["dJ_ci95"][1] < 0 and b["dJ_ci95"][1] < 0
        ]
        if common:
            a, b = min(common, key=lambda ab: ab[0]["dJ_ci95"][1] + ab[1]["dJ_ci95"][1])
            row[comps[0]], row[comps[1]] = f"{a['id']} {_fmt_ci(a)}", f"{b['id']} {_fmt_ci(b)}"
            both.append(row)
        rows.append(row)
    out.append(
        f"* Records with a v2 result: {len(q2)}; candidates whose paired CI is entirely below 0 against BOTH "
        f"{comps[0]} and {comps[1]} simultaneously on at least one (the same) target cell: **{len(both)}**."
    )
    if both:
        out += [
            "",
            f"| candidate | method | decision | winning target cell vs {comps[0]} (dJ [95% CI]) | vs {comps[1]} |",
            "|---|---|---|---|---|",
        ]
        out += [
            f"| {x['id']} | {x['method']} | {x['dec']} | {x[comps[0]]} | {x[comps[1]]} |"
            for x in both
        ]
    else:
        out.append(
            "* No candidate beats both controls on the same target cell with a paired CI excluding 0."
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
        "| candidate | method | decision | effect | best target cell (comparator) dJ [95% CI] | beats VALID-applicable simple controls (vacuously True if none valid) | validity | v1-regression |",
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


NOTES = [
    "## Run notes and A1 interpretation choices (read before using the numbers)",
    "",
    "* Strongest applicable comparator = per cell, lowest mean J among comparators whose promotion rate on the candidate's validity cells (cells where its claimed null holds) is <= 0.10; the host is subject to the same filter. Candidates claiming no null (economic/none) face all comparators. `never_switch` is a comparator, so on null cells and on several alternative cells it is the strongest and every label-spending candidate is compared with it.",
    "* The registered Gap-Mix `exact0.8_s4` adapter declares claimed null `marg` (A1 text says conditional-null); on all v2 cells cond and marg truths coincide, so no comparator validity decision depends on this.",
    "* Control-cell regression (section 4 item 2) is evaluated against the same per-cell strongest comparator, as registered; this is a strict test (never_switch is cheapest on null cells).",
    "* Suite-v2 hosts are `calibrated_v1`; one `native_v0` host run per cell is stored in each record (`results.native_v0_reference`), never used as a comparator. A candidate worse than its host on a v1 cell it ran on (paired CI above 0) is not KEEP; the tranche-1 records are the source.",
    "* Scope (i-ii) 33+14 flags overlap on 6 identities (`scope: [i, ii]`). Canary identities need the family 'RAR-native persistent drift' that v2 does not provide: they stay UNVERIFIED by construction.",
    "* Reference runs were sharded into seed chunks of 2 (paired runs are independent per seed, so concatenation equals one run). Gap-Mix `exact0.8_s4` took up to ~11 CPU-minutes per seed on S2c (cap = T, lognormal delay) and emits numerical RuntimeWarnings (divide by zero / overflow in `sota/inrepo/gapmix.py`) on some cells; the adapter is frozen and was not changed.",
    "* Cache keys use a code hash pinned at launch (`SHIFTLAB_STAGE_B_CODE_HASH`). Another agent added the opt-in Q1 evidence seam to `adapters_drift2act.py` in the same worktree during the run; the default path is unchanged (its golden test passes), and the hash at launch covers the pre-seam sources.",
    "* Scope (iii) cap: after a first launch measured the 300 s limit on wall-clock under 12-way contention, 6 early CRASH records (wall-clock timeouts, identities `dual_null_reporting` and `min_of_both_certificate`) were appended; the experiment cap was then measured as 300 CPU seconds of the worker process tree (a 16-cell experiment needs 40-270 CPU-s alone) and those identities were re-run and decided (CRASH records stay in the ledger). Four `restart_mixture_allocation` identities exceed 300 CPU-s and are CRASH (cpu_cap) - retryable only with a larger cap or fewer cells, which A1 does not allow.",
    "* Scope (iii) cells: the v1 section-3 Q1 row (4 cells) plus the 12 v2 cells with label_cap < T and no informative delay/missingness (S2a-c have cap = T, i.e. a degenerate gap schedule). Shell = `adapters_evidence.promoter_adapter`, calendar schedule, alpha 0.1. The Drift2Act-host run with the identity's evidence is reported only for two v1 cells (`results.descriptive_drift2act_host_runs`) and is OUT_OF_CONTRACT for validity. Scope (iii) fully reports every `required_baselines` entry outside the registered Q1 comparator set in `required_baselines_outside_scope_iii_set`.",
    "",
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
    lines += NOTES
    lines += [
        "Ledger: `docs/d2a_rar/registry/EXPERIMENT_LEDGER.jsonl`; logs: `results/d2a_rar/stage_b/stage_b_t2_run.log`, `stage_b_t2_iii_run.log`.",
        "",
    ]
    return "\n".join(lines)
