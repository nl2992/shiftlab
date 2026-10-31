"""Build docs/hgxh2c/FINAL_REPORT.md from whatever outputs exist.

Expected outputs/hgxh2c/stage4/confirmation.json schema:
  {"finalists": {<id>: {
      "vs_baseline": {<baseline_id>: {"mean", "lo", "hi", "p"}},   # Delta_J = J_base - J_cand, p one-sided
      "holm_p": float, "iut_pass": bool,
      "ablations": {<channel>: {"mean", "lo", "hi"}},
      "negative_control": {"mean", "lo", "hi"},                    # time-shuffled source
      "power_diff": {"mean", "lo", "hi"},                          # vs frontier, 800-step window
      "regime_wins": {<regime>: bool}}},
   # optional extra fields written by stage4_confirm.py (not required here):
   #   per finalist: ctx_replace {mean,lo,hi} (J_ctxONS-replaced - J_full), absolute_gain, relative_gain, regime_table,
   #   negative_transfer_regimes, secondary_unadjusted {far (Clopper-Pearson), labels, delay, cost_components, runtime_s},
   #   outcome; top level: selector (same shape as a finalist), baselines, best_baseline, config.
   # ablations / negative_control means are J_ablated (or J_shifted) - J_full: positive = the channel / alignment helps.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/hgxh2c"
NR = "_not run yet_"


def jload(p):
    p = Path(p)
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def git(*a):
    return subprocess.run(
        ["git", *a], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


ALIAS = {
    "independent": ("indep",),
    "contextual": ("ctx_ons", "contextual"),
    "multivariate": ("ryu", "multivariate"),
}


def beats(v, key):
    ks = [
        k for k in v.get("vs_baseline", {}) if any(a in k.lower() for a in ALIAS.get(key, (key,)))
    ]
    return bool(ks) and all(
        v["vs_baseline"][k]["p"] < 0.05 and v["vs_baseline"][k]["mean"] > 0 for k in ks
    )


def decide(v):
    """PROTOCOL section 10 decision table for one finalist. The verdict refers to the PRIMARY family (anytime-valid frontier
    members, A5); the secondary comparison (CUSUM / Page-Hinkley) is appended."""
    out = _decide(v)
    sec = v.get("secondary_status")
    return f"{out} [family: primary anytime-valid{'; vs CUSUM/PH: ' + sec if sec else ''}]"


def _decide(v):
    wins = v.get("regime_wins", {})
    if v.get("iut_pass") and v.get("holm_p", 1) < 0.05:
        if wins and all(wins.values()):
            return "beats all strong baselines across regimes, valid: stronger conference candidate"
        return "beats all applicable baselines in one regime: promising scoped result"
    if beats(v, "independent") and not beats(v, "contextual"):
        return "beats independent HG+H2c, not contextual ONS: useful combination, weak novelty"
    if beats(v, "contextual") and not beats(v, "multivariate"):
        return "beats contextual ONS, not multivariate betting: task-specific; narrow novelty claim"
    j_any = any(r["p"] < 0.05 and r["mean"] > 0 for r in v.get("vs_baseline", {}).values())
    pw = (v.get("power_diff") or {}).get("lo", -1) > 0
    if pw and not j_any:
        return "better detection, not better J: monitoring contribution only"
    if j_any and not pw:
        return "better J, not better detection: decision-policy contribution"
    return "nothing survives: negative result; keep the failure atlas and stop the mechanism"


def section_stage1():
    p = ROOT / "docs/hgxh2c/02_NATIVE_REPRODUCTION.md"
    if not p.exists():
        return NR
    rows = [ln for ln in p.read_text("utf-8").splitlines() if ln.startswith("|")]
    base = "\n".join(rows) if rows else f"{p.name} exists but has no status table."
    try:
        return base + "\n\n" + repro_compare()
    except Exception as e:  # noqa: BLE001  the reduced/full/paper comparison is optional
        return base + f"\n\n(reduced/full/paper comparison unavailable: {e!r})"


def repro_compare():
    """Reduced vs paper-budget (stage1_full) vs paper values; 'Full' is n/a until `run_native_repro.py --full` has produced results."""
    import functools
    import statistics as st

    s1 = ROOT / "outputs/hgxh2c/stage1"
    red = jload(s1 / "reduced_summary.json") or {}
    ful = jload(ROOT / "outputs/hgxh2c/stage1_full/full_summary.json") or {}
    pv = jload(ROOT / "scripts/hgxh2c/stage1/paper_values.json") or {}
    f = lambda x, d=2: (
        "n/a" if x is None else (f"{x:.{d}f}" if isinstance(x, (int, float)) else str(x))
    )
    g = lambda d, *k: functools.reduce(lambda a, b: a.get(b) if isinstance(a, dict) else None, k, d)
    L = [
        (
            "Reproduction vs paper (`outputs/hgxh2c/stage1/reduced_summary.json`, `outputs/hgxh2c/stage1_full/full_summary.json`, "
            f"`scripts/hgxh2c/stage1/paper_values.json`). Paper-budget results present: {bool(ful.get('found'))}."
        ),
        "",
        "| Experiment | Metric | Reduced | Full (paper budget) | Paper |",
        "|---|---|---|---|---|",
    ]
    for fam, key in (
        ("label shift", "tenzer_label_shift"),
        ("concept shift", "tenzer_concept_shift"),
    ):
        for k, r in (red.get(key) or {}).items():
            fr = (ful.get(key) or {}).get(k) or {}
            for stat in (
                "baselines",
                "imputed_with_baselines",
                "PPI",
                "PPI_positive_lambda",
                "lrt_y",
            ):
                L.append(
                    f"| Tenzer {fam} {k.split('/')[-1][:-4]} | power {stat} | {f(g(r, 'power', stat))} (n={r['reps']}) | "
                    f"{f(g(fr, 'power', stat))} (n={fr.get('reps', 'n/a')}) | imputed > without; 1-sided PPI > 2-sided (figures) |"
                )
    for var, tr in (
        ("approx_w0", "eprocess"),
        ("approx_w200", "eprocess"),
        ("grapa_w200", "eprocess"),
        ("approx_w200", "running_risk"),
    ):
        r, fr = g(red, "timans", var, tr), g(ful, "timans", var, tr)
        L.append(
            f"| Timans exp_uci {var} | {tr} mean delay / false-alarm rate | {f(g(r, 'mean_delay'), 1)} / {f(g(r, 'false_alarm_rate'), 3)} "
            f"(trials {g(r, 'trials')}) | {f(g(fr, 'mean_delay'), 1)} / {f(g(fr, 'false_alarm_rate'), 3)} (trials {g(fr, 'trials')}) | "
            "wealth process lowest delay among guaranteed trackers (qualitative) |"
        )
    for m in ("label all", "oblivious", "learned"):
        r, fr = g(red, "xu", "beta_hat", m), g(ful, "xu", "beta_hat", m)
        L.append(
            f"| Xu simulation | beta-hat {m} | {f(g(r, 'mean'), 3)} (n={g(r, 'n')}) | {f(g(fr, 'mean'), 3)} (n={g(fr, 'n')}) | "
            f"beta*={g(pv, 'xu', 'beta_star')}; learned lower than all/oblivious |"
        )
    for k in ("srm", "pp_fixed", "pp_adapt"):
        r, fr = g(red, "pprm", "drift", k), g(ful, "pprm", "drift", k)
        L.append(
            f"| PPRM independent (synthetic) | mean alarm t {k} | {f(g(r, 'mean_alarm_t'), 1)} | {f(g(fr, 'mean_alarm_t'), 1)} | "
            "CIFAR10-C 760 (PPRM) / 800 (SRM); LLM ~500 / ~530 |"
        )
    r, fr = (
        g(red, "pprm", "nominal", "pp_adapt", "alarm_rate"),
        g(ful, "pprm", "nominal", "pp_adapt", "alarm_rate"),
    )
    L.append(
        f"| PPRM independent (synthetic) | false-alarm rate (nominal) | {f(r, 3)} | {f(fr, 3)} | <= {g(pv, 'pprm', 'pfa_bound')} |"
    )
    for q, v in (ful.get("pprm_reliance_sweep") or {}).items():
        L.append(
            f"| PPRM reliance sweep q_pred={q} | paired adaptive - fixed (steps) | n/a | "
            f"{f(g(v, 'paired_pp_adapt_minus_pp_fixed', 'mean'), 1)} | Table 1: -11 to -21 |"
        )
    r = g(red, "ryu_scalar", "problems") or {}
    fr = g(ful, "ryu_scalar", "problems") or {}
    for prob in ("beta1,3", "beta10,10"):
        for m in ("UP", "PRECiSE_CO96"):
            a, b = g(r, prob, m, "width_T"), g(fr, prob, m, "width_T")
            L.append(
                f"| Ryu scalar {prob} | final CI width {m} | {f(st.mean(a), 4) if a else 'n/a'} | "
                f"{f(st.mean(b), 4) if b else 'n/a'} | UP tightest (figure only) |"
            )
    return "\n".join(L)


def section_stage2():
    import pandas as pd

    s, fr = OUT / "stage2/summary.parquet", jload(OUT / "stage2/frontier.json")
    if not s.exists():
        return NR
    df = pd.read_parquet(s)
    t = f"summary rows: {len(df)}; methods: {df.method_id.nunique()}; cells: {df.cell_id.nunique()}\n"
    if fr:
        t += f"\nfrontier (track|cell) entries: {len(fr.get('frontier', fr))}; flagged empirical-alarm: {fr.get('flagged', [])}\n"
        t += f"\nexcluded for FAR: {fr.get('excluded', {})}\n"
    return t


def section_stage3():
    import pandas as pd

    r, fin = OUT / "stage3/registry.parquet", jload(OUT / "stage3/finalists.json")
    if not r.exists():
        return NR
    df = pd.read_parquet(r)
    t = f"registry rows: {len(df)}\n"
    for c in ("rung", "reason"):
        if c in df:
            t += f"\ncounts by {c}:\n\n```\n{df[c].value_counts(dropna=False).sort_index().to_string()}\n```\n"
    fin_txt = "```json\n" + json.dumps(fin, indent=1)[:4000] + "\n```" if fin else NR
    return t + "\nfinalists:\n\n" + fin_txt + "\n"


def section_stage4():
    c = jload(OUT / "stage4/confirmation.json")
    if not c:
        return NR
    t = ""
    for fid, v in c.get("finalists", {}).items():
        t += f"\n### {fid}\n\nOutcome (PROTOCOL section 10): **{decide(v)}**\n\n"
        t += f"Primary family (anytime-valid): Holm p = {v.get('holm_p')}, IUT pass = {v.get('iut_pass')}\n\n"
        if "holm_p_secondary" in v:
            t += f"Secondary family (CUSUM/PH, non-anytime-valid): Holm p = {v.get('holm_p_secondary')}, IUT pass = {v.get('iut_pass_secondary')}, status = {v.get('secondary_status')}\n\n"
        t += "| baseline | Delta_J | 95% CI | p (1-sided) |\n|---|---|---|---|\n"
        for b, r in v.get("vs_baseline", {}).items():
            t += f"| {b} | {r['mean']:.4g} | [{r['lo']:.4g}, {r['hi']:.4g}] | {r['p']:.4g} |\n"
        for k in ("ablations", "negative_control", "power_diff", "regime_wins"):
            t += f"\n{k} (secondary, unadjusted CIs): `{json.dumps(v.get(k))}`\n"
    return t


def figures():
    d = ROOT / "tmp/papervizagent"
    if d.exists():
        sys.path.insert(0, str(d))
        try:
            import importlib.util

            if any(importlib.util.find_spec(n) for n in ("papervizagent", "paperbanana")):
                return "PaperBanana importable; figures come from a separate PaperBanana step (none generated here)."
        except ImportError:  # find_spec on a dotted/odd name; treat as unavailable
            pass
    return "PaperBanana unavailable: figures not generated"


def main():
    parts = [
        ("Stage 1: native reproduction", section_stage1),
        ("Stage 2: common benchmark and frontier", section_stage2),
        ("Stage 3: combinatorial search", section_stage3),
        ("Stage 4: confirmation", section_stage4),
    ]
    md = [
        "# HG x H2c final report",
        "",
        "Protocol: docs/hgxh2c/PROTOCOL.md. Generated by scripts/hgxh2c/make_report.py.",
        "",
    ]
    md += [
        f"Git commit: `{git('rev-parse', 'HEAD')}`; dirty: {bool(git('status', '--porcelain'))}",
        "",
    ]
    for title, fn in parts:
        try:
            body = fn()
        except Exception as e:  # noqa: BLE001 - one failing section must not abort the whole report
            body = f"report section failed: {e!r}"
        md += [f"## {title}", "", body, ""]
    md += [
        "## Figures", "", figures(), "", "## Reproduce", "", "```",
        "PYTHONPATH=src .venv/Scripts/python.exe scripts/hgxh2c/pipeline.py --status",
        "PYTHONPATH=src .venv/Scripts/python.exe scripts/hgxh2c/pipeline.py [--only stageN]", "```", "",
    ]  # fmt: skip
    out = ROOT / "docs/hgxh2c/FINAL_REPORT.md"
    out.write_text("\n".join(md), "utf-8")
    print("wrote", out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
