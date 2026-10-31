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
    """PROTOCOL section 10 decision table for one finalist."""
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
    return "\n".join(rows) if rows else f"{p.name} exists but has no status table."


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
        t += f"Holm p = {v.get('holm_p')}, IUT pass = {v.get('iut_pass')}\n\n"
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
