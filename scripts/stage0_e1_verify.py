"""Stage 0 / T0.2: independent E1 verifier.

Recomputes headline numbers from frozen row-level artifacts using only numpy, pandas,
pyarrow and scipy. It does NOT import shiftlab or any original analysis script. Original
analysis scripts were read only to learn column semantics and the recorded bootstrap
procedure (seed 20261027, B = 10,000, paired resampling of seeds). Summary and decision
files are read only AFTER recomputation, to compare.

Run:  uv run --no-sync python scripts/stage0_e1_verify.py
Writes docs/research_refinement_v1/stage0/e1_verification.json. CPU only; no experiment reruns.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads
from scipy.stats import beta, binom

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research_refinement_v1/stage0/e1_verification.json"
CMP = ROOT / "outputs/gated_monitor_compare"
NUL = ROOT / "outputs/gated_monitor_null"
EIA = ROOT / "outputs/eia_real_data_validity"
INT = ROOT / "outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1"
TAB = ROOT / "docs/phase_tables_stratified_monitor"

CHECKS: list[dict] = []
HASHES: list[dict] = []


def add(claim, recomputed, claimed, tol, note="", status=None, kind="numeric"):
    """Record one check. tol is an absolute tolerance (half a unit in the last reported digit)."""
    if status is None:
        if recomputed is None:
            status = "MISSING"
        elif kind == "numeric":
            status = "PASS" if abs(float(recomputed) - float(claimed)) <= tol + 1e-12 else "FAIL"
        else:
            status = "PASS" if recomputed == claimed else "FAIL"
    CHECKS.append(
        {
            "claim": claim,
            "recomputed": recomputed,
            "claimed": claimed,
            "tolerance": tol,
            "status": status,
            "note": note,
        }
    )


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_check(label, path: Path, expected: str | None, source: str):
    actual = sha256(path)
    if actual is None:
        status = "MISSING"
    elif expected is None:
        status = "NO_RECORDED_HASH"
    else:
        status = "MATCH" if actual == expected else "MISMATCH"
    HASHES.append(
        {
            "artifact": label,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": actual,
            "recorded": expected,
            "recorded_in": source,
            "status": status,
        }
    )


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------- hashes
def do_hashes():
    cm = jload(CMP / "manifest.json")["outputs_sha256"]
    cam = jload(CMP / "analysis/manifest.json")
    nm = jload(NUL / "manifest.json")["outputs_sha256"]
    nam = jload(NUL / "analysis/manifest.json")
    em = jload(EIA / "manifest.json")["outputs_sha256"]
    im = jload(INT / "manifest.json")
    readme = (TAB / "README.md").read_text(encoding="utf-8")

    def readme_hash(name):  # hash in the README table row for this file
        for line in readme.splitlines():
            if line.startswith(f"| `{name}`"):
                parts = [c.strip().strip("`") for c in line.split("|")]
                return parts[3]
        return None

    for f in ("streams.parquet", "decision.json", "launch.json"):
        hash_check(
            f"compare/{f}", CMP / f, cm.get(f), "outputs/gated_monitor_compare/manifest.json"
        )
    hash_check(
        "compare/streams.parquet (analysis input)",
        CMP / "streams.parquet",
        cam["input_sha256"],
        "compare/analysis/manifest.json:input_sha256",
    )
    for f in ("summary.csv", "decision.json"):
        hash_check(
            f"compare/analysis/{f}",
            CMP / "analysis" / f,
            cam["output_sha256"][f],
            "compare/analysis/manifest.json",
        )
    hash_check(
        "compare/analysis/summary.csv vs README",
        CMP / "analysis/summary.csv",
        readme_hash("wp1_s3_comparison_summary.csv"),
        "docs/phase_tables_stratified_monitor/README.md",
    )
    hash_check(
        "docs copy wp1_s3_comparison_summary.csv",
        TAB / "wp1_s3_comparison_summary.csv",
        readme_hash("wp1_s3_comparison_summary.csv"),
        "docs/phase_tables_stratified_monitor/README.md",
    )
    for f in ("streams.parquet", "decision.json", "launch.json"):
        hash_check(f"null/{f}", NUL / f, nm.get(f), "outputs/gated_monitor_null/manifest.json")
    hash_check(
        "null/streams.parquet (analysis input)",
        NUL / "streams.parquet",
        nam["input_sha256"],
        "null/analysis/manifest.json:input_sha256",
    )
    for f in ("summary.csv", "decision.json"):
        hash_check(
            f"null/analysis/{f}",
            NUL / "analysis" / f,
            nam["output_sha256"][f],
            "null/analysis/manifest.json",
        )
    hash_check(
        "null/analysis/summary.csv vs README",
        NUL / "analysis/summary.csv",
        readme_hash("wp1_null_summary.csv"),
        "docs/phase_tables_stratified_monitor/README.md",
    )
    hash_check(
        "docs copy wp1_null_summary.csv",
        TAB / "wp1_null_summary.csv",
        readme_hash("wp1_null_summary.csv"),
        "docs/phase_tables_stratified_monitor/README.md",
    )
    for f, readme_name in (
        ("injected.csv", "wp4_eia_injected.csv"),
        ("null_cells.csv", "wp4_eia_null_cells.csv"),
        ("unmodified.csv", "wp4_eia_unmodified.csv"),
        ("decision.json", None),
    ):
        hash_check(f"eia/{f}", EIA / f, em.get(f), "outputs/eia_real_data_validity/manifest.json")
        if readme_name:
            hash_check(
                f"eia/{f} vs README",
                EIA / f,
                readme_hash(readme_name),
                "docs/phase_tables_stratified_monitor/README.md",
            )
            hash_check(
                f"docs copy {readme_name}",
                TAB / readme_name,
                readme_hash(readme_name),
                "docs/phase_tables_stratified_monitor/README.md",
            )
    # integrated confirmation
    hash_check(
        "efficacy_100_v1/integrated_pipeline_seed_metrics.parquet",
        INT / "integrated_pipeline_seed_metrics.parquet",
        im.get("metrics_sha256"),
        "efficacy_100_v1/manifest.json:metrics_sha256",
    )
    hash_check(
        "efficacy_100_v1/integrated_pipeline_summary.csv",
        INT / "integrated_pipeline_summary.csv",
        im.get("summary_sha256"),
        "efficacy_100_v1/manifest.json:summary_sha256",
    )
    hash_check(
        "efficacy_100_v1/integrated_pipeline_paired_contrasts.csv",
        INT / "integrated_pipeline_paired_contrasts.csv",
        im.get("paired_contrasts_sha256"),
        "efficacy_100_v1/manifest.json:paired_contrasts_sha256",
    )
    hash_check(
        "efficacy_100_v1/protocol_snapshot.md",
        INT / "protocol_snapshot.md",
        im.get("protocol_snapshot_sha256"),
        "efficacy_100_v1/manifest.json:protocol_snapshot_sha256",
    )
    hash_check(
        "efficacy_100_v1/evaluator_event_log.parquet",
        INT / "evaluator_event_log.parquet",
        im["evaluator_event_log"]["sha256"],
        "efficacy_100_v1/manifest.json:evaluator_event_log",
    )
    hash_check(
        "efficacy_100_v1/learner_event_log.parquet",
        INT / "learner_event_log.parquet",
        im["learner_event_log"]["sha256"],
        "efficacy_100_v1/manifest.json:learner_event_log",
    )


# ----------------------------------------------------------------------------- H1 / H2 / H3 (S3)
def paired_ratio_bootstrap(num, den, seed=20261027, B=10_000):
    """Paired percentile bootstrap of mean(num)/mean(den), resampling stream indices jointly."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(len(num), size=(B, len(num)))
    n_b, d_b = num[idx].mean(axis=1), den[idx].mean(axis=1)
    draws = np.where(d_b > 0, n_b / np.where(d_b > 0, d_b, 1.0), -np.inf)
    return (
        num.mean() / den.mean(),
        float(np.quantile(draws, 0.025)),
        float(np.quantile(draws, 0.975)),
    )


def do_s3():
    d = pd.read_parquet(CMP / "streams.parquet")
    d = d[
        d.scenario.eq("boundary_local_harm") & d.arm.eq("gated_ht_paced") & d.engine.eq("fixed08")
    ]
    # H1
    g = d[d.budget_rate.eq(0.20)].sort_values("seed")
    assert len(g) == 100 and g.seed.is_unique
    est, lo, hi = paired_ratio_bootstrap(g.growth_vs_uniform_ppi, g.comparator_growth_uniform_ppi)
    note = (
        "ratio of means of per-stream best-fixed-stake post-onset growth (stored per row; the underlying "
        "e-process paths are not stored). CI reproduces the recorded procedure: seed 20261027, B=10000, "
        "default_rng.integers, percentile 2.5/97.5"
    )
    add("H1 growth ratio gated-HT/uniform-PPI, r=0.20 (point)", round(est, 6), 7.2014, 5e-5, note)
    add("H1 bootstrap 95% CI lower", round(lo, 6), 6.8845, 5e-5, note)
    add("H1 bootstrap 95% CI upper", round(hi, 6), 7.5512, 5e-5, note)
    # own-seed procedure-level CI
    _, lo2, hi2 = paired_ratio_bootstrap(
        g.growth_vs_uniform_ppi, g.comparator_growth_uniform_ppi, seed=777, B=20_000
    )
    add(
        "H1 CI, independent seed 777 B=20000 (procedure-level)",
        [round(lo2, 4), round(hi2, 4)],
        [6.8845, 7.5512],
        0.05,
        "Monte Carlo sampling difference expected; PASS if endpoints within 0.05 of claimed",
        status="PASS" if abs(lo2 - 6.8845) <= 0.05 and abs(hi2 - 7.5512) <= 0.05 else "FAIL",
        kind="vec",
    )
    # H1 McNemar at r = 0.05
    raw = pd.read_parquet(CMP / "streams.parquet")
    b = raw[
        raw.scenario.eq("boundary_local_harm") & raw.budget_rate.eq(0.05) & raw.engine.eq("fixed08")
    ]
    a = b[b.arm.eq("gated_ht_paced")].set_index("seed").detected.astype(int).sort_index()
    u = b[b.arm.eq("uniform_ppi")].set_index("seed").detected.astype(int).sort_index()
    assert a.index.equals(u.index) and len(a) == 100
    wins, losses = int(((a == 1) & (u == 0)).sum()), int(((a == 0) & (u == 1)).sum())
    p = (
        float(binom.sf(wins - 1, wins + losses, 0.5)) if wins + losses else 1.0
    )  # P(X >= wins), exact one-sided
    add(
        "H1 McNemar discordant wins (gated-HT detects, uniform-PPI not), r=0.05",
        wins,
        100,
        0.0,
        kind="numeric",
    )
    add("H1 McNemar discordant losses", losses, 0, 0.0)
    add(
        "H1 McNemar exact one-sided p, r=0.05",
        p,
        7.9e-31,
        5e-33,
        "tolerance = half unit in last digit of 7.9e-31; exact value is 0.5**100",
    )
    # spend
    lab = b.groupby("arm")[["labels", "dollars"]].mean()
    add(
        "H1 spend labels gated-HT (r=0.05)",
        round(lab.loc["gated_ht_paced", "labels"], 4),
        118.1,
        0.05,
    )
    add("H1 spend labels uniform-PPI", round(lab.loc["uniform_ppi", "labels"], 4), 114.1, 0.05)
    add("H1 spend dollars gated-HT", round(lab.loc["gated_ht_paced", "dollars"], 4), 177.3, 0.05)
    add("H1 spend dollars uniform-PPI", round(lab.loc["uniform_ppi", "dollars"], 4), 170.9, 0.05)
    # H2
    for r, claimed in ((0.02, 17.47), (0.05, 20.61), (0.10, 14.73), (0.20, 7.20)):
        c = d[d.budget_rate.eq(r)]
        assert len(c) == 100
        val = c.growth_vs_uniform_ppi.mean() / c.comparator_growth_uniform_ppi.mean()
        add(
            f"H2 observed growth ratio r={r:.2f}",
            round(float(val), 6),
            claimed,
            0.005,
            "analytic predictions 18/18/15/7.5 are pre-registered constants, not recomputed",
        )
    # H3 S3
    h = raw[raw.scenario.eq("harmful_adaptation") & raw.budget_rate.eq(0.10)]
    det = h.groupby(["arm", "engine"]).detected.mean()
    for arm, claimed, lbl in (
        ("gated_ht_fixed", 0.86, "default mixture fixed"),
        ("gated_ht_paced", 0.76, "default mixture paced"),
        ("gated_ht_fixed__timans_grapa", 0.94, "GRAPA fixed"),
        ("gated_ht_paced__timans_grapa", 0.91, "GRAPA paced"),
    ):
        val = det.xs(arm, level="arm").iloc[0]
        add(
            f"H3 S3 harmful_adaptation r=0.10 detection, {lbl}",
            round(float(val), 4),
            claimed,
            0.005,
            "default mixture = engine fixed08; GRAPA = timans_grapa",
        )
    # cross-check against the committed phase table copy
    tab = pd.read_csv(TAB / "wp1_s3_comparison_summary.csv")
    t = (
        tab[tab.scenario.eq("harmful_adaptation") & tab.budget_rate.eq(0.10)]
        .set_index("arm")
        .detection
    )
    ok = all(
        abs(t[k] - v) <= 5e-3
        for k, v in (
            ("gated_ht_fixed", 0.86),
            ("gated_ht_paced", 0.76),
            ("gated_ht_fixed__timans_grapa", 0.94),
            ("gated_ht_paced__timans_grapa", 0.91),
        )
    )
    add("H3 S3 phase-table CSV agrees with claimed values", ok, True, 0, kind="exact")
    # compare to their decision.json (after recomputation)
    dec = jload(CMP / "analysis/decision.json")
    add(
        "H1 own point estimate vs decision.json p1.estimate",
        est,
        dec["p1"]["estimate"],
        1e-9,
        "summary-vs-recompute",
    )
    add(
        "H1 own CI lower vs decision.json",
        lo,
        dec["p1"]["lower_95_two_sided"],
        1e-9,
        "summary-vs-recompute",
    )
    add(
        "H1 own CI upper vs decision.json",
        hi,
        dec["p1"]["upper_95_two_sided"],
        1e-9,
        "summary-vs-recompute",
    )


# ----------------------------------------------------------------------------- H3 EIA
def do_eia():
    d = pd.read_csv(EIA / "injected.csv")
    key = ["respondent", "window", "onset_fraction"]
    ff = d[d.arm.eq("full_feedback")].set_index(key)
    detectable = ff.index[ff.detection_rate > 0]
    add(
        "H3 EIA number of detectable cells (12 path-onset cells less 2 non-detectable)",
        len(detectable),
        10,
        0,
    )
    for r in (0.05, 0.10, 0.20):
        fx = d[d.arm.eq("gated_ht_fixed") & np.isclose(d.budget, r)].set_index(key)
        m = sum(
            bool(
                fx.loc[k, "detection_rate"] == 1.0
                and fx.loc[k, "median_delay_events"] == ff.loc[k, "median_delay_events"]
            )
            for k in detectable
        )
        add(
            f"H3 EIA fixed matches full-feedback median delay, r={r:.2f} (of detectable cells)",
            m,
            10,
            0,
            "match = fixed detection_rate == 1 and median_delay_events equal; hourly data so events == hours",
        )
        # also hours
        mh = sum(
            bool(fx.loc[k, "median_delay_hours"] == ff.loc[k, "median_delay_hours"])
            for k in detectable
        )
        add(f"H3 EIA same test on median_delay_hours, r={r:.2f}", mh, 10, 0)


# ----------------------------------------------------------------------------- H4
def do_h4():
    ds = pads.dataset(INT / "evaluator_event_log.parquet")
    t = ds.to_table(
        columns=[
            "scenario",
            "seed",
            "method",
            "expected_incumbent_minus_deployed_gain",
            "intervention_cost_units",
        ],
        filter=pads.field("method").isin(["q1_fallback", "full_pipeline"]),
    ).to_pandas()
    g = t.groupby(["scenario", "seed", "method"], sort=True).sum().reset_index()
    # net expected gain = oracle expected gain summed over events minus intervention cost units
    g["net"] = g.expected_incumbent_minus_deployed_gain - g.intervention_cost_units
    assert (g.groupby(["scenario", "method"]).seed.nunique() == 100).all()
    mean = g.groupby(["scenario", "method"]).net.mean()
    claims = [
        ("boundary_local_harm", "q1_fallback", 664.64),
        ("harmful_adaptation_at_monitor", "q1_fallback", 685.91),
        ("recurring_regimes", "q1_fallback", 447.96),
        ("boundary_local_harm", "full_pipeline", 118.01),
        ("harmful_adaptation_at_monitor", "full_pipeline", 161.16),
        ("recurring_regimes", "full_pipeline", 0.0),
        ("post_promotion_reversal", "q1_fallback", -1148.46),
        ("post_promotion_reversal", "full_pipeline", -143.76),
    ]
    for sc, me, c in claims:
        add(
            f"H4 mean net expected gain {sc} / {me}",
            round(float(mean[(sc, me)]), 6),
            c,
            0.005,
            "from evaluator_event_log: sum(expected gain) - sum(intervention_cost_units), mean of 100 seeds",
        )
    # compare against stored per-seed metric & summary
    m = pd.read_parquet(INT / "integrated_pipeline_seed_metrics.parquet")
    j = g.merge(m, on=["scenario", "seed", "method"])
    dev = float((j.net - j.expected_deployment_gain).abs().max())
    add(
        "H4 event-log net vs seed_metrics.expected_deployment_gain, max abs per-seed deviation",
        dev,
        0.0,
        1e-9,
        "definition check of 'expected gain' (cost coefficient 1)",
    )
    s = (
        pd.read_csv(INT / "integrated_pipeline_summary.csv")
        .set_index(["scenario", "method"])
        .mean_expected_gain
    )
    dev2 = max(abs(float(mean[k]) - float(s[k])) for k in mean.index)
    add(
        "H4 recomputed means vs integrated_pipeline_summary.csv mean_expected_gain, max abs deviation",
        dev2,
        0.0,
        1e-9,
    )


# ----------------------------------------------------------------------------- S2 null
def cp_upper(k, n, family):
    return 1.0 if k == n else float(beta.ppf(1 - 0.05 / family, k + 1, n - k))


def do_s2():
    d = pd.read_parquet(
        NUL / "streams.parquet",
        columns=["arm", "scenario", "budget_rate", "seed", "false_alarm", "feature_false_alarm"],
    )
    d["fa"] = d.false_alarm.astype(bool)
    fe = d.arm.eq("feature_adwin")
    d.loc[fe, "fa"] = d.loc[fe, "feature_false_alarm"].astype(
        bool
    )  # sentinel arm uses its own feature alarm
    d = d[~fe | d.scenario.eq("stationary")]
    want = set(range(58_500_000, 58_502_000))
    keys = ["arm", "scenario", "budget_rate"]
    seeds_ok = all(set(g.seed) == want and len(g) == 2000 for _, g in d.groupby(keys))
    add(
        "S2 every cell has exactly the 2,000 seeds 58500000-58501999",
        seeds_ok,
        True,
        0,
        kind="exact",
    )
    t = d.groupby(keys).agg(alarms=("fa", "sum"), n=("seed", "size")).reset_index()
    fam = t.groupby("arm").size()
    t["family"] = t.arm.map(fam)
    t["upper"] = [cp_upper(int(r.alarms), int(r.n), int(r.family)) for r in t.itertuples()]
    add("S2 number of arms", int(t.arm.nunique()), 41, 0)
    worst = t.groupby("arm").upper.max()
    add(
        "S2 arms with simultaneous exact upper bound <= 5%",
        int((worst <= 0.05).sum()),
        int(t.arm.nunique()),
        0,
    )
    add(
        "S2 max upper bound over all arms/cells (claim: <= 5%)",
        round(float(worst.max()), 6),
        0.05,
        0.0,
        "PASS if recomputed <= 0.05",
        status="PASS" if worst.max() <= 0.05 else "FAIL",
    )
    # compare to the analysis summary after recomputation
    s = pd.read_csv(NUL / "analysis/summary.csv")
    j = t.merge(s, on=keys, suffixes=("", "_s"))
    add("S2 per-cell alarm counts equal summary.csv", int((j.alarms != j.alarms_s).sum()), 0, 0)
    add(
        "S2 per-cell upper bounds equal summary.csv, max abs deviation",
        float((j.upper - j.simultaneous_exact_upper).abs().max()),
        0.0,
        1e-9,
    )
    add("S2 cells compared", len(j), len(s), 0)
    # documented primary-arm table (docs/gated_monitor_null_calibration_results.md, 3 decimals in percent)
    doc = {
        ("stationary", 0.02): (0, 0.253),
        ("stationary", 0.05): (1, 0.358),
        ("stationary", 0.10): (4, 0.613),
        ("stationary", 0.20): (6, 0.764),
        ("benign_nuisance", 0.02): (0, 0.253),
        ("benign_nuisance", 0.05): (2, 0.449),
        ("benign_nuisance", 0.10): (4, 0.613),
        ("benign_nuisance", 0.20): (6, 0.764),
    }
    p = t[t.arm.eq("gated_ht_paced")].set_index(["scenario", "budget_rate"])
    for (sc, r), (k, ub) in doc.items():
        add(
            f"S2 gated_ht_paced {sc} r={r:.2f} alarms / upper bound %",
            [int(p.loc[(sc, r), "alarms"]), round(float(100 * p.loc[(sc, r), "upper"]), 3)],
            [k, ub],
            0.0005,
            "doc table: alarms/2000 and bound in percent to 3 decimals",
            status="PASS"
            if int(p.loc[(sc, r), "alarms"]) == k
            and abs(100 * p.loc[(sc, r), "upper"] - ub) <= 0.0005 + 1e-12
            else "FAIL",
            kind="vec",
        )
    top = worst.sort_values(ascending=False)
    ppe = t[t.arm.eq("ppe_gated")]
    add(
        "S2 doc: largest bound anywhere 1.953% (ppe_gated, 24/2000)",
        [top.index[0], int(ppe.alarms.max()), round(100 * float(top.iloc[0]), 3)],
        ["ppe_gated", 24, 1.953],
        0.0005,
        status="PASS"
        if (
            top.index[0] == "ppe_gated"
            and int(ppe.alarms.max()) == 24
            and abs(100 * top.iloc[0] - 1.953) <= 0.0005
        )
        else "FAIL",
        kind="vec",
    )
    nxt = t[t.arm.eq("gated_ht_paced__fixed1")]
    add(
        "S2 doc: next-largest 1.115% (gated_ht_paced__fixed1, 11/2000)",
        [top.index[1], int(nxt.alarms.max()), round(100 * float(top.iloc[1]), 3)],
        ["gated_ht_paced__fixed1", 11, 1.115],
        0.0005,
        status="PASS"
        if (
            top.index[1] == "gated_ht_paced__fixed1"
            and int(nxt.alarms.max()) == 11
            and abs(100 * top.iloc[1] - 1.115) <= 0.0005
        )
        else "FAIL",
        kind="vec",
    )
    # per-arm false-alarm count summary for the report
    per_arm = (
        t.groupby("arm")
        .agg(
            total_alarms=("alarms", "sum"),
            max_cell_alarms=("alarms", "max"),
            cells=("alarms", "size"),
        )
        .join(worst.rename("max_upper"))
    )
    return per_arm.reset_index().to_dict(orient="records")


# ----------------------------------------------------------------------------- WP4 nulls
def do_wp4():
    n = pd.read_csv(EIA / "null_cells.csv")
    prim = n[np.isclose(n.epsilon, 0.1)]
    zero = n[np.isclose(n.epsilon, 0.0)]
    add(
        "WP4 primary (epsilon=0.1) null cells with 0 alarms / 1000 (claim 68/68)",
        f"{int(((prim.alarms == 0) & (prim.replicates == 1000)).sum())}/{len(prim)}",
        "68/68",
        0,
        kind="exact",
    )
    add("WP4 primary total alarms across the 68 cells", int(prim.alarms.sum()), 0, 0)
    k = len(prim)
    bound = float(beta.ppf(1 - 0.05 / k, 1, 1000))
    add(
        f"WP4 all-cell Bonferroni exact one-sided upper bound, {k} primary cells, percent",
        round(100 * bound, 4),
        0.72,
        0.005,
        "0/1000 closed form 1-(alpha/k)^(1/1000) = 0.7189%; claim '~0.72%'; tolerance half unit of last digit",
    )
    assert abs(bound - (1 - (0.05 / k) ** (1 / 1000))) < 1e-12
    rec = np.array(
        [
            1.0 if a == r else float(beta.ppf(0.95, a + 1, r - a))
            for a, r in zip(n.alarms, n.replicates)
        ]
    )
    add(
        "WP4 null_cells.csv cp_upper recomputed (one-sided 95%, unadjusted) max abs deviation",
        float(np.abs(rec - n.cp_upper).max()),
        0.0,
        1e-8,
    )
    add(
        "WP4 arms in null cells",
        sorted(n.arm.unique().tolist()),
        sorted(
            ["full_feedback", "gated_eb_paced", "gated_ht_fixed", "gated_ht_paced", "ungated_ht"]
        ),
        0,
        kind="exact",
    )
    # Informational: the epsilon=0 rows are the descriptive null boundary, NOT part of the 68/68 claim.
    add(
        "WP4 INFO epsilon=0 (descriptive null boundary) cells with 0 alarms / total",
        f"{int((zero.alarms == 0).sum())}/{len(zero)}; total alarms {int(zero.alarms.sum())}; max cell {int(zero.alarms.max())}/1000",
        "not claimed (docs call epsilon=0 descriptive)",
        0,
        status="INFO",
        kind="vec",
        note="README row description says 'primary and epsilon = 0'; the 68/68 claim holds only for primary epsilon=0.1. "
        "A reader taking 136 rows as 68/68 would be wrong; at epsilon=0 the orientation null is not a null for the bound.",
    )


def main() -> int:
    do_hashes()
    do_s3()
    do_eia()
    do_h4()
    per_arm = do_s2()
    do_wp4()

    w = max(len(c["claim"]) for c in CHECKS)
    print(f"{'claim':<{min(w, 100)}} | recomputed | claimed | tol | status")
    for c in CHECKS:
        print(
            f"{c['claim'][:100]:<{min(w, 100)}} | {c['recomputed']} | {c['claimed']} | {c['tolerance']} | {c['status']}"
        )
    print("\nHASH CHECKS")
    for h in HASHES:
        print(f"{h['status']:<18} {h['artifact']}  {h['sha256']}")
    nfail = sum(c["status"] == "FAIL" for c in CHECKS) + sum(
        h["status"] in ("MISMATCH", "MISSING") for h in HASHES
    )
    print(
        f"\n{len(CHECKS)} checks, {sum(c['status'] == 'PASS' for c in CHECKS)} PASS, {sum(c['status'] == 'FAIL' for c in CHECKS)} FAIL, "
        f"{sum(c['status'] == 'MISSING' for c in CHECKS)} MISSING; hash mismatches/missing: "
        f"{sum(h['status'] in ('MISMATCH', 'MISSING') for h in HASHES)}"
    )

    def clean(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
            return str(o)
        raise TypeError(type(o))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"checks": CHECKS, "hashes": HASHES, "s2_per_arm": per_arm}, indent=2, default=clean
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
