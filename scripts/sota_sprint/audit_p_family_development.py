#!/usr/bin/env python3
"""Reconcile key P-family development tables against frozen records.

This is a descriptive numerical audit, not a validity test. It checks deterministic P1 summary
statistics and the published P2 V1/V2, P4 null/power, and P5 synthetic paired-cost tables.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def markdown_table(text: str, marker: str) -> tuple[list[str], list[list[str]]]:
    tail = text.split(marker, 1)[1]
    lines = []
    started = False
    for line in tail.splitlines():
        if line.strip().startswith("|"):
            started = True
            lines.append(line.strip())
        elif started:
            break
    cells = [[c.strip() for c in line.strip("|").split("|")] for line in lines]
    return cells[0], cells[2:]


def report_check(name: str, mismatches: list[str], cells: int) -> dict:
    return {"name": name, "status": "PASS" if not mismatches else "FAIL",
            "cell_count": cells, "difference_count": len(mismatches),
            "differences": mismatches[:30]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("docs/sprint2/family_p/development_audit.json"))
    args = ap.parse_args()
    checks: list[dict] = []

    # P1: exact summary convention used by analyze.py: means for metrics, medians for promotion times.
    p1 = pd.read_json(ROOT / "outputs/sprint2/P/dev_syn/records.jsonl", lines=True)
    saved = json.loads((ROOT / "docs/sprint2/family_p/dev_syn_P1.json").read_text())
    colmap = {"net": "net", "promote": "ever_promote", "rollbacks": "n_rollbacks",
              "labels": "labels", "switches": "switches", "regret": "regret_expected_oracle",
              "pending": "max_pending", "runtime": "runtime_s"}
    mismatches = []
    cells = 0
    for (regime, policy), g in p1.groupby(["regime", "policy"]):
        if regime not in saved or policy not in saved[regime]["policies"]:
            mismatches.append(f"missing saved P1 cell {regime}/{policy}")
            continue
        out = saved[regime]["policies"][policy]
        computed = {k: float(g[col].mean()) for k, col in colmap.items()}
        for k, col in (("first", "first_deploy"), ("delay", "detect_delay")):
            v = g.loc[g[col] >= 0, col]
            computed[k] = float(v.median()) if len(v) else -1.0
        for metric, value in computed.items():
            cells += 1
            if metric not in out or not np.isclose(round(value, 3), float(out[metric]), atol=0.00101, rtol=0):
                mismatches.append(f"{regime}/{policy}/{metric}: {round(value,3)} != {out.get(metric)}")
    checks.append(report_check("P1 development summary", mismatches, cells))

    # P1_power.md selects representative paired ΔJ claims from the 23-regime screen. Recompute
    # each displayed mean/normal interval directly from paired raw seed records (candidate - A5b).
    p1_power = (ROOT / "docs/sprint2/family_p/P1_power.md").read_text()
    _, displayed_rows = markdown_table(p1_power, "| regime | P1_renew | P1_union | P1_sui_fixedgap (ablation: no renewal) | P1_A5b_c10 |")
    candidate_columns = [("P1_renew", 1), ("P1_union", 2), ("P1_sui_fixedgap", 3), ("P1_A5b_c10", 4)]
    regime_map = {
        "F5_dep_better_r8 (targeted)": ["F5_dep_better_r8"],
        "S_dep_better_r95 (targeted)": ["S_dep_better_r95"],
        "F0_better (iid)": ["F0_better"],
        "F9_bursty_better": ["F9_bursty_better"],
        "P_hmm_better / P_piecerho_better": ["P_hmm_better", "P_piecerho_better"],
        "S_reversal_400": ["S_reversal_400"],
    }
    p1_table_mismatches, p1_table_cells = [], 0
    for row in displayed_rows:
        if len(row) < 5:
            continue
        display_regime = row[0]
        actual_regimes = regime_map.get(display_regime)
        if actual_regimes is None:
            p1_table_mismatches.append(f"unrecognized P1 power-table row: {display_regime}")
            continue
        for candidate, col in candidate_columns:
            def paired_summary(regime):
                paired = p1[p1.regime == regime].pivot_table(
                    index=["ep", "seed"], columns="policy", values="net")
                if candidate not in paired or "A5b" not in paired:
                    return None
                delta = (paired[candidate] - paired["A5b"]).dropna().to_numpy()
                if len(delta) < 2:
                    return None
                mean = float(delta.mean())
                se = float(delta.std(ddof=1) / np.sqrt(len(delta)))
                return (mean, mean - 1.96 * se, mean + 1.96 * se)

            expected_by_regime = [paired_summary(regime) for regime in actual_regimes]
            if any(value is None for value in expected_by_regime):
                p1_table_mismatches.append(f"missing raw paired source {candidate}/{display_regime}")
                continue
            if candidate == "P1_A5b_c10" and len(expected_by_regime) > 1:
                # The report abbreviates both near-zero paired effects as one “~0”.
                expected_by_regime = [tuple(np.mean([v[i] for v in expected_by_regime]) for i in range(3))]
            shown_parts = row[col].split("/") if len(actual_regimes) > 1 and candidate != "P1_A5b_c10" else [row[col]]
            if len(shown_parts) != len(expected_by_regime):
                p1_table_mismatches.append(f"expected {len(expected_by_regime)} paired values for {candidate}/{display_regime}")
                continue
            for expected, shown_part in zip(expected_by_regime, shown_parts):
                shown_match = re.search(r"([+−-]?\d+(?:\.\d+)?|~0)(?:\s*\[\s*([+−-]?\d+(?:\.\d+)?)\s*,\s*([+−-]?\d+(?:\.\d+)?)\s*\])?", shown_part)
                if shown_match is None:
                    p1_table_mismatches.append(f"unparseable P1 contrast {candidate}/{display_regime}")
                    continue
                displayed_mean = "0" if shown_match.group(1) == "~0" else shown_match.group(1)
                p1_table_cells += 1
                shown_decimals = len(displayed_mean.split(".", 1)[1]) if "." in displayed_mean else 0
                if not np.isclose(expected[0], float(displayed_mean.replace("−", "-")),
                                  atol=0.5 * 10 ** (-shown_decimals) if shown_decimals else 0.50001,
                                  rtol=0):
                    p1_table_mismatches.append(f"{candidate}/{display_regime} mean: {expected[0]} != {displayed_mean}")
                if shown_match.group(2) is not None:
                    for source_value, shown_value, label in zip(expected[1:], shown_match.groups()[1:], ("lo", "hi")):
                        p1_table_cells += 1
                        shown_decimals = len(shown_value.split(".", 1)[1]) if "." in shown_value else 0
                        if not np.isclose(source_value, float(shown_value.replace("−", "-")),
                                          atol=0.5 * 10 ** (-shown_decimals) + 1e-9, rtol=0):
                            p1_table_mismatches.append(f"{candidate}/{display_regime} {label}: {source_value} != {shown_value}")
    checks.append(report_check("P1 selected power-repair contrast table", p1_table_mismatches, p1_table_cells))

    # P1's free-text null claim distinguishes the nine other null regimes from the additional
    # out-of-class HMM stress. Reconcile each stated 0/20 and 3/20 count to the raw seed records.
    designated_nulls = ["F0_null", "F5_dep_null_r8", "F5_dep_null_r95", "O_null_order2",
                        "O_null_semimarkov", "P_bursty_null_r8", "P_markov_null_r98",
                        "P_order2_null", "P_piecerho_null"]
    p1_null_claims = (ROOT / "docs/sprint2/family_p/P1_power.md").read_text()
    null_policies = ["P1_renew", "P1_union", "P1_sui_fixedgap", "P1_A5b_c10"]
    null_mismatches, null_cells = [], 0
    for regime in designated_nulls:
        for policy in null_policies:
            g = p1[(p1.regime == regime) & (p1.policy == policy)]
            null_cells += 1
            if len(g) != 20 or int(g.ever_promote.sum()) != 0:
                null_mismatches.append(f"{policy}/{regime}: {int(g.ever_promote.sum())}/{len(g)} not 0/20")
    for policy, expected_count in (("P1_renew", 0), ("P1_union", 0), ("P1_sui_fixedgap", 0),
                                   ("P1_A5b_c10", 3), ("A5b", 3)):
        g = p1[(p1.regime == "P_hmm_null") & (p1.policy == policy)]
        null_cells += 1
        if len(g) != 20 or int(g.ever_promote.sum()) != expected_count:
            null_mismatches.append(f"{policy}/P_hmm_null: {int(g.ever_promote.sum())}/{len(g)} != {expected_count}/20")
    for phrase in ("nine other screened null regimes", "out-of-class",
                   "matched A5b at 3/20 (.15)"):
        null_cells += 1
        if phrase not in p1_null_claims:
            null_mismatches.append(f"P1 null narrative omits scoped claim: {phrase}")
    checks.append(report_check("P1 null-promotion narrative and scope", null_mismatches, null_cells))

    # P1: reconcile the displayed Fisher and representative log-evidence tables to p1diag output.
    p1diag = json.loads((ROOT / "outputs/sprint2/P/p1diag/p1diag.json").read_text())
    p1doc = (ROOT / "docs/sprint2/family_p/P1_power.md").read_text()
    fish_header, fish_rows = markdown_table(p1doc, "**Fisher information**")
    fish_saved = {round(float(r[0]), 2): r for r in fish_rows}
    fish_by_a = {round(float(r["a"]), 2): r for r in p1diag["fisher_p0.6"]}
    p1diag_mismatches = []
    p1diag_cells = 0
    for a in (0.0, 0.25, 0.5, 0.8, 0.95):
        row = fish_saved.get(a)
        src = fish_by_a.get(a)
        if row is None or src is None:
            p1diag_mismatches.append(f"missing Fisher row a={a}")
            continue
        for col, key in (("I(p), rho known", "I_known"), ("I_eff(p), rho free", "I_free"), ("ratio", "ratio")):
            expected = round(float(src[key]), 2)
            observed = float(row[fish_header.index(col)])
            p1diag_cells += 1
            if not np.isclose(expected, observed, atol=0.011, rtol=0):
                p1diag_mismatches.append(f"Fisher/a={a}/{col}: {expected} != {observed}")
    sim_header, sim_rows = markdown_table(p1doc, "**Simulation**")
    sim_saved = {}
    for row in sim_rows:
        try:
            p_txt, rho_txt, gap_txt = [part.strip() for part in row[0].split(",")]
            key = (round(float(p_txt), 2), round(float(rho_txt), 2), int(gap_txt.split("=")[-1]))
            sim_saved[key] = row
        except (ValueError, IndexError):
            continue
    sim_src = {(round(float(r["p"]), 2), round(float(r["rho"]), 2), int(r["G"])): r for r in p1diag["sim"]}
    for key in ((.65,.8,1),(.65,.8,7),(.65,.8,12),(.65,.95,7),(.65,0.0,1)):
        row, src = sim_saved.get(key), sim_src.get(key)
        if row is None or src is None:
            p1diag_mismatches.append(f"missing simulation row {key}")
            continue
        for col, metric in (("oracle","oracle"),("single-start SUI","sui"),
                            ("absorbed by null sup","absorbed"),("alt-mixture misfit","alt_loss"),
                            ("renewal","renewal")):
            expected = round(float(src[metric]), 1)
            observed = float(row[sim_header.index(col)])
            p1diag_cells += 1
            if not np.isclose(expected, observed, atol=0.051, rtol=0):
                p1diag_mismatches.append(f"simulation/{key}/{col}: {expected} != {observed}")
    checks.append(report_check("P1 displayed diagnostic tables", p1diag_mismatches, p1diag_cells))

    # P2: rates are episode-level over all 120 null episodes, with any qualifying promotion counted once.
    p2 = json.loads((ROOT / "outputs/sprint2/P/p2p3/p2p3.json").read_text())
    p2doc = (ROOT / "docs/sprint2/family_p/P2P3_objectives_harm.md").read_text()
    policies = ["A5b", "gated_adaptive_range+front", "rmm:gated_deployment+RMM", "D2", "QSG", "P3_follow"]
    null_eps = [r for r in p2["synthetic"] if r["p"] <= 0.5]
    table = p2doc.split("| policy | V2 | V1 |", 1)[1].split("\n\n", 1)[0]
    saved_rates = {}
    for name, v2, v1 in re.findall(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", table, re.M):
        try:
            saved_rates[name.strip()] = (float(v2), float(v1))
        except ValueError:  # Markdown separator row
            continue
    mismatches = []
    display_to_policy = {"RMM (gated)": "rmm:gated_deployment+RMM"}
    for policy in policies:
        rows = [r for r in null_eps if r["policy"] == policy]
        v2 = sum(bool(r["promotions"]) for r in rows) / len(rows)
        v1 = sum(any(float(pr["Cpol500"]) <= 0 for pr in r["promotions"]) for r in rows) / len(rows)
        actual = (round(v2, 3), round(v1, 3))
        display = next((k for k,v in display_to_policy.items() if v == policy),policy)
        if actual != saved_rates.get(display):
            mismatches.append(f"{policy}: computed {actual}, report {saved_rates.get(display)}")
    checks.append(report_check("P2 episode-level V1/V2 table", mismatches, 2 * len(policies)))
    # P2 twin A_500 summaries are per-promotion averages over 40 episodes per stream.
    twin_report = re.search(r"Twin real streams.*?A5b ([+-]?\d+(?:\.\d+)?) \((\d+)% of promotions positive\),\s*GAR\+front\s*([+-]?\d+(?:\.\d+)?) \((\d+)%\),\s*RMM\s*([+-]?\d+(?:\.\d+)?) \((\d+)%\),\s*D2\s*([+-]?\d+(?:\.\d+)?) \((\d+)%\)",p2doc,re.S)
    twin_mismatches=[]
    twin_cells=0
    if not twin_report:
        twin_mismatches.append("could not parse P2 twin A_500 sentence")
    else:
        stored=list(twin_report.groups())
        actual=[float(stored[i]) if i%2==0 else float(stored[i]) for i in range(8)]
        twin_cells=8
        for display,policy,mi,fi in [("A5b","A5b",0,1),("GAR+front","gated_adaptive_range+front",2,3),
                                     ("RMM","rmm:gated_deployment+RMM",4,5),("D2","D2",6,7)]:
            prs=[pr for run in p2["twin"] if run["policy"]==policy for pr in run["promotions"]]
            vals=[float(pr["A500"]) for pr in prs]
            m=round(float(np.mean(vals)),1) if vals else float("nan")
            pct=round(100*float(np.mean(np.asarray(vals)>0))) if vals else float("nan")
            if m!=actual[mi] or pct!=actual[fi]:twin_mismatches.append(f"{display}: computed {m}/{pct}, report {actual[mi]}/{actual[fi]}")
    checks.append(report_check("P2 twin A500 outcomes",twin_mismatches,twin_cells))

    # P2: selected-promotion correlations/conditional harms quoted in the narrative.
    # These are descriptive pooled-promotion quantities, not independent-unit inference.
    p2_narrative_mismatches = []
    p2_narrative_cells = 0
    for rho, delay, expected in (
        (0.0, 100, (0.86, 0.86, 0.86)),
        (0.8, 100, (0.74, 0.74, 0.74)),
        (0.95, 1, (0.24, 0.24, 0.24)),
        (0.95, 100, (0.52, 0.53, 0.52)),
    ):
        promos = [pr for run in p2["synthetic"]
                  if float(run["rho"]) == rho and int(run["delay"]) == delay
                  for pr in run["promotions"]]
        for target, reported in zip(("M500", "Cstate500", "Cpol500"), expected):
            actual = float(np.corrcoef(
                [float(pr["A500"]) for pr in promos],
                [float(pr[target]) for pr in promos],
            )[0, 1])
            p2_narrative_cells += 1
            if round(actual, 2) != reported:
                p2_narrative_mismatches.append(
                    f"rho={rho}/delay={delay}/{target}: {actual:.4f} != {reported:.2f}")
    for delay, expected in ((1, 8.6), (100, -2.9)):
        vals = [float(pr["A500"]) for run in p2["synthetic"]
                if float(run["p"]) == 0.5 and float(run["rho"]) == 0.95
                and int(run["delay"]) == delay for pr in run["promotions"]]
        actual = float(np.mean(vals))
        p2_narrative_cells += 1
        if round(actual, 1) != expected:
            p2_narrative_mismatches.append(
                f"rho=.95 null mean A500 delay={delay}: {actual:.4f} != {expected:.1f}")
    checks.append(report_check("P2 narrative correlations and conditional harm",
                               p2_narrative_mismatches, p2_narrative_cells))

    # P3: selected harm values against never-switch, conditional on a promotion.
    base = { (r["p"],r["rho"],r["delay"],r["seed"]):r["net"]
             for r in p2["synthetic"] if r["policy"] == "CONTROL_never_switch" }
    # Extract the first table following the P3 heading (the markdown parser needs a heading marker).
    p3header, p3rows = markdown_table(p2doc,"ΔJ against never switch, cs = 5")
    p3policies = {"D2":"D2", "QSG":"QSG", "GAR+front":"gated_adaptive_range+front",
                  "RMM":"rmm:gated_deployment+RMM", "P3_follow":"P3_follow"}
    p3_mismatches=[]
    p3cells=0
    for row in p3rows:
        disp, rho_text = row[0], row[1]
        policy=p3policies.get(disp)
        if policy is None: continue
        rho=float(rho_text.replace(".95","0.95").replace(".8","0.8"))
        for col, p, delay in (("p=.45, d=1",.45,1),("p=.45, d=100",.45,100),
                              ("p=.5, d=1",.5,1),("p=.5, d=100",.5,100)):
            vals=[]
            for run in p2["synthetic"]:
                if (run["policy"]==policy and run["p"]==p and run["rho"]==rho and
                    run["delay"]==delay and run["promotions"]):
                    vals.append(run["net"]-base[(p,rho,delay,run["seed"])])
            idx=p3header.index(col)
            observed=float(row[idx])
            computed=float(np.mean(vals)) if vals else float("nan")
            p3cells+=1
            if not np.isclose(round(computed,1),observed,atol=0.051,rtol=0):
                p3_mismatches.append(f"{disp}/rho={rho}/{col}: {computed} != {observed}")
    checks.append(report_check("P3 selected promotion-harm cells",p3_mismatches,p3cells))

    # P4: raw null-promotion rates and alternative mean costs against both Markdown tables.
    p4 = pd.read_json(ROOT / "outputs/sprint2/P/dev_syn/records.jsonl", lines=True)
    p4doc = (ROOT / "docs/sprint2/family_p/P4_misspecification.md").read_text()
    nullmap = {"Markov r8": "F5_dep_null_r8", "r95": "F5_dep_null_r95",
               "r98": "P_markov_null_r98", "bursty r8": "P_bursty_null_r8",
               "order2 (O)": "O_null_order2", "order2 (P)": "P_order2_null",
               "semi-Markov": "O_null_semimarkov", "HMM": "P_hmm_null", "piece-rho": "P_piecerho_null"}
    altmap = {"Markov r8": "F5_dep_better_r8", "order2": "P_order2_better",
              "semi-Markov": "P_semimarkov_better", "HMM": "P_hmm_better",
              "piece-rho": "P_piecerho_better"}
    null_header, null_rows = markdown_table(p4doc, "## False promotion on V2 nulls")
    mismatches = []
    for row in null_rows:
        policy = row[0].replace("**", "")
        policy = {"RMM (gated)": "rmm:gated_deployment+RMM"}.get(policy, policy)
        for header, regime in nullmap.items():
            idx = null_header.index(header)
            expected = float(p4[(p4.policy == policy) & (p4.regime == regime)].ever_promote.mean())
            observed = float(row[idx].replace("**", ""))
            if not np.isclose(round(expected, 2), observed, atol=0.0051, rtol=0):
                mismatches.append(f"null/{policy}/{header}: {round(expected,2)} != {observed}")
    null_cells = sum(len(r)-1 for r in null_rows)
    cost_header, cost_rows = markdown_table(p4doc, "## Mean net cost J on misspecified alternatives")
    for row in cost_rows:
        policy = {"RMM (gated)": "rmm:gated_deployment+RMM", "never switch": "CONTROL_never_switch"}.get(
            row[0].replace("**", ""), row[0].replace("**", ""))
        for header, regime in altmap.items():
            idx = cost_header.index(header)
            expected = float(p4[(p4.policy == policy) & (p4.regime == regime)].net.mean())
            observed = float(row[idx].replace("**", ""))
            if not np.isclose(round(expected), observed, atol=0.51, rtol=0):
                mismatches.append(f"alt/{policy}/{header}: {round(expected)} != {observed}")
    checks.append(report_check("P4 null rates and alternative costs", mismatches,
                               null_cells + sum(len(r)-1 for r in cost_rows)))

    # P5: paired K_D2 - comparator means and normal 95% half-widths for the six synthetic regimes.
    kdata = json.loads((ROOT / "outputs/sprint2/P/kscreen/kscreen.json").read_text())["rows"]
    kdf = pd.DataFrame([r for r in kdata if r["kind"] == "syn"])
    p5doc = (ROOT / "docs/sprint2/family_p/P5_multimodel.md").read_text()
    p5header, p5rows = markdown_table(p5doc, "Paired ΔJ of K_D2 against each comparator")
    comp = ["K_cams", "K_model_picker", "K_never", "K_D2-host_only"]
    mismatches = []
    nchecked = 0
    for row in p5rows:
        regime = row[0]
        if regime not in set(kdf.regime):
            continue  # real-data descriptive table uses episode-level units, not this paired seed table
        g = kdf[kdf.regime == regime].pivot(index=["ep", "seed"], columns="policy", values="net")
        for j, comparator in enumerate(comp, start=1):
            d = (g["K_D2"] - g[comparator]).to_numpy()
            mean = float(d.mean())
            half = float(1.96 * d.std(ddof=1) / np.sqrt(len(d)))
            cell = row[j]
            match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:±\s*([0-9]+(?:\.\d+)?))?", cell)
            if not match:
                mismatches.append(f"{regime}/{comparator}: unparsed '{cell}'")
            else:
                observed_mean = float(match.group(1))
                observed_half = float(match.group(2)) if match.group(2) is not None else None
                if round(mean, 1) != observed_mean or (observed_half is not None and round(half, 1) != observed_half):
                    mismatches.append(f"{regime}/{comparator}: computed {mean:+.1f} ± {half:.1f}, report {cell}")
            nchecked += 1
    checks.append(report_check("P5 synthetic paired-cost table", mismatches, nchecked))
    realdf=kdf  # retain synthetic frame for common schema; add real rows from source artifact
    realdf=pd.DataFrame([r for r in kdata if r["kind"]=="real"])
    p5_real_m=[]; p5_real_cells=0
    for row in p5rows:
        title=row[0]
        match=re.match(r"real ([^(]+) \((\d+)(?: episodes)?\)",title)
        if not match:continue
        ds=match.group(1).strip()
        g0=realdf[realdf.regime==ds]
        paired=g0.pivot(index="ep",columns="policy",values="net")
        for j,comparator in enumerate(comp,start=1):
            d=(paired["K_D2"]-paired[comparator]).dropna().to_numpy()
            mean=round(float(d.mean()),1)
            half=round(float(1.96*d.std(ddof=1)/np.sqrt(len(d))),1)
            cell=row[j]
            om=re.search(r"[+-]?\d+(?:\.\d+)?",cell)
            hm=re.search(r"±\s*(\d+(?:\.\d+)?)",cell)
            p5_real_cells+=1
            if (not om or float(om.group())!=mean or not hm or float(hm.group(1))!=half):
                p5_real_m.append(f"{ds}/{comparator}: computed {mean:+.1f} ± {half:.1f}, report {cell}")
    checks.append(report_check("P5 real-data paired-cost means and intervals",p5_real_m,p5_real_cells))

    # P5 real K=4 stream construction: verify the first two columns still match the frozen 2-model cache.
    kstream_stats=json.loads((ROOT/"outputs/sprint2/P/kstreams/stats.json").read_text())["streams"]
    kstream_m=[]; kstream_cells=0
    for item in kstream_stats:
        name=item["dataset"]
        losses=np.load(ROOT/f"outputs/sprint2/P/kstreams/{name}.npz")["L"]
        ref=np.load(ROOT/f"data/sprint_fresh_losses/{name}.npz")
        for col,key in ((0,"l0"),(1,"l1")):
            same=bool(np.array_equal(losses[:,:,col],ref[key]))
            kstream_cells+=1
            if not same or not item.get("matches_2model_cache"):
                kstream_m.append(f"{name}/column{col}: cache equality failed")
    checks.append(report_check("P5 K=4 first-two-column cache identity",kstream_m,kstream_cells))

    # P5 prose: savings counts, null-switch reduction, and real-stream CI attribution.
    p5_claim_m=[]; p5_claim_cells=0
    syn_diff={}
    for regime,g in kdf.groupby("regime"):
        pivot=g.pivot(index=["ep","seed"],columns="policy",values="net")
        syn_diff[regime]=float((pivot["K_D2"]-pivot["K_cams"]).mean())
    syn_better=sum(v<0 for v in syn_diff.values())
    p5_claim_cells+=1
    if syn_better!=4:
        p5_claim_m.append(f"K_D2 cheaper than native CAMS on {syn_better}/6 synthetic settings, report says 4/6")
    real_better=0; real_sig=set()
    for ds,g in realdf.groupby("regime"):
        pivot=g.pivot(index="ep",columns="policy",values="net")
        delta=(pivot["K_D2"]-pivot["K_cams"]).dropna().to_numpy()
        real_better+=int(float(delta.mean())<0)
        half=1.96*float(delta.std(ddof=1))/np.sqrt(len(delta))
        if float(delta.mean())-half>0 or float(delta.mean())+half<0:
            real_sig.add(ds)
    p5_claim_cells+=2
    if real_better!=5:
        p5_claim_m.append(f"K_D2 cheaper than native CAMS on {real_better}/5 real datasets, report says 5/5")
    if real_sig!={"household_power","metro"}:
        p5_claim_m.append(f"real K_D2/native-CAMS paired CIs exclude zero for {sorted(real_sig)}")
    null=kdf[kdf.regime.isin(["K3_null","K4_null"])]
    rates=null.groupby(["regime","policy"]).ever_switch.mean()
    k_rates=[float(rates.loc[(reg,pol)]) for reg in ("K3_null","K4_null")
             for pol in ("K_D2","K_cams","K_model_picker")]
    p5_claim_cells+=1
    if not np.allclose(k_rates,[.05,1.0,.95,.05,1.0,1.0]):
        p5_claim_m.append(f"K3/K4 null switch rates differ from report: {k_rates}")
    checks.append(report_check("P5 cost, confidence-interval and null-switch prose",p5_claim_m,p5_claim_cells))

    # P6: seed-paired development contrasts; newer P6 records replace earlier rows for these policies.
    p6dev=pd.concat([pd.read_json(ROOT/"outputs/sprint2/P/dev_syn/records.jsonl",lines=True),
                     pd.read_json(ROOT/"outputs/sprint2/P/dev_p6/records.jsonl",lines=True)],ignore_index=True)
    p6dev=p6dev.drop_duplicates(["regime","seed","policy"],keep="last")
    p6doc=(ROOT/"docs/sprint2/family_p/P6_late_reversal.md").read_text()
    p6header,p6rows=markdown_table(p6doc,"## 2. Screen results (development)")
    regimes=["F1_late_800","F1_late_1200","W_late_1000","F3_reversal_800","S_reversal_400","F0_better","F5_dep_better_r8"]
    p6pairs={"P6_LRMD_U vs M_LRMD_SUI":("P6_LRMD_U","M_LRMD_SUI"),
             "P6_LRMD_U vs `xu_acquisition_only` (Xu acquisition + ShiftLab paired certificate)":("P6_LRMD_U","xu_acquisition_only"),
             "P6_RRD vs A5b":("P6_RRD","A5b"),
             "P6_RRD vs M_RMMSUI_A5b":("P6_RRD","M_RMMSUI_A5b")}
    p6_mismatches=[]; p6cells=0
    for row in p6rows:
        key=row[0]
        pair=p6pairs.get(key)
        if pair is None: continue
        a,b=pair
        for idx,regime in enumerate(regimes,start=1):
            vals=p6dev[p6dev.regime==regime].pivot(index="seed",columns="policy",values="net")
            d=(vals[a]-vals[b]).dropna().to_numpy()
            mean=float(d.mean()); half=1.96*float(d.std(ddof=1))/np.sqrt(len(d)) if len(d)>1 else 0
            cell=row[idx]
            m=re.search(r"([+-]?\d+(?:\.\d+)?)(?:\s*\[\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\])?",cell)
            p6cells+=1
            if not m:
                p6_mismatches.append(f"{key}/{regime}: unparsed {cell!r}"); continue
            observed_mean=float(m.group(1))
            if round(mean,1)!=observed_mean:
                p6_mismatches.append(f"{key}/{regime}/mean: {mean} != {observed_mean}")
            if m.group(2) is not None and (round(mean-half,1)!=float(m.group(2)) or round(mean+half,1)!=float(m.group(3))):
                p6_mismatches.append(f"{key}/{regime}/CI: computed [{mean-half:.1f},{mean+half:.1f}] != [{m.group(2)},{m.group(3)}]")
    checks.append(report_check("P6 synthetic development paired contrasts",p6_mismatches,p6cells))
    # P6 fresh-real table reports mean net cost by dataset, averaged over source episodes.
    p6real=pd.concat([pd.read_json(ROOT/"outputs/sprint2/P/dev_real/records.jsonl",lines=True),
                      pd.read_json(ROOT/"outputs/sprint2/P/dev_real_p6/records.jsonl",lines=True)],ignore_index=True)
    p6real=p6real.drop_duplicates(["regime","ep","policy"],keep="last")
    real_table_start=p6doc.split("**Fresh real mean J**",1)[1]
    rtables=[]
    lines=[]
    in_table=False
    for line in real_table_start.splitlines():
        if line.strip().startswith("|"):
            in_table=True;lines.append(line.strip())
        elif in_table:break
    rcells=[[c.strip() for c in line.strip("|").split("|")] for line in lines]
    real_rows=rcells[2:]
    data_names=["appliances","beijing_pm25","bike_hour","household_power","metro"]
    mismatches=[]; cells=0
    for row in real_rows:
        policy=row[0]
        for idx,ds in enumerate(data_names,start=1):
            value=float(p6real[(p6real.policy==policy)&(p6real.regime==ds)].net.mean())
            obs=float(row[idx]);cells+=1
            if round(value)!=obs:mismatches.append(f"{policy}/{ds}: {round(value)} != {obs}")
    checks.append(report_check("P6 fresh-real mean-cost table",mismatches,cells))

    # P3: every cost-reweighted cell is a deterministic function of fixed cs=5 records and switches.
    p3sweep = json.loads((ROOT / "docs/sprint2/family_p/P3_cost_sweep.json").read_text())
    p3_source = json.loads((ROOT / "outputs/sprint2/P/p2p3/p2p3.json").read_text())["synthetic"]
    p3_mismatch = []
    p3_cells = 0
    for summary in p3sweep["rows"]:
        matching = [r for r in p3_source if float(r["p"]) == float(summary["p"])
                    and float(r["rho"]) == float(summary["rho"])
                    and int(r["delay"]) == int(summary["delay"])]
        means = {}
        for policy in sorted({r["policy"] for r in matching}):
            vals = [float(r["net"]) + (float(summary["switch_cost"])-5.0)*float(r["switches"])
                    for r in matching if r["policy"] == policy]
            means[policy] = float(np.mean(vals))
        if not means:
            p3_mismatch.append(f"missing source rows {summary}")
            continue
        best_other = min((k for k in means if k != "P3_follow"), key=means.get)
        expected = {"P3_follow_mean_J": means["P3_follow"],
                    "best_other": best_other,
                    "best_other_mean_J": means[best_other],
                    "P3_minus_best_other": means["P3_follow"]-means[best_other],
                    "best_policy": min(means, key=means.get)}
        for key, value in expected.items():
            p3_cells += 1
            got = summary.get(key)
            same = got == value if isinstance(value, str) else np.isclose(float(got), value, atol=1e-10, rtol=1e-12)
            if not same:
                p3_mismatch.append(f"{summary['p']}/{summary['rho']}/{summary['delay']}/cs={summary['switch_cost']}/{key}: {got} != {value}")
        for policy, value in means.items():
            p3_cells += 1
            if policy not in summary["policy_mean_J"] or not np.isclose(float(summary["policy_mean_J"][policy]), value, atol=1e-10, rtol=1e-12):
                p3_mismatch.append(f"{summary['p']}/{summary['rho']}/{summary['delay']}/cs={summary['switch_cost']}/{policy}: stored policy mean differs")
    checks.append(report_check("P3 full switch-cost reweighting", p3_mismatch, p3_cells))

    # P3: verify the prose's cost-grid wins and explicitly scoped delay-100/full-grid loss ranges.
    p3_claim_mismatches = []
    p3_claim_cells = 0
    rows = p3sweep["rows"]
    short_wins = [r["P3_minus_best_other"] for r in rows
                  if r["rho"] == 0.95 and r["delay"] == 1 and r["switch_cost"] <= 2.0]
    extra_win = [r["P3_minus_best_other"] for r in rows
                 if r["p"] == 0.5 and r["rho"] == 0.8 and r["delay"] == 1
                 and r["switch_cost"] == 0.5]
    delay100 = [r["P3_minus_best_other"] for r in rows if r["delay"] == 100]
    all_grid = [r["P3_minus_best_other"] for r in rows]
    claims = [
        ("rho=.95 delay=1 cs<=2 win range", min(short_wins), -79.5),
        ("rho=.95 delay=1 cs<=2 win range", max(short_wins), -11.6),
        ("p=.5 rho=.8 delay=1 cs=.5 additional win", extra_win[0], -1.8),
        ("delay=100 loss lower endpoint", min(delay100), 14.0),
        ("delay=100 loss upper endpoint", max(delay100), 669.5),
        ("full-grid loss maximum", max(all_grid), 738.4),
    ]
    for label, actual, reported in claims:
        p3_claim_cells += 1
        if round(float(actual), 1) != reported:
            p3_claim_mismatches.append(f"{label}: computed {actual:.4f}, report {reported:.1f}")
    p3doc = (ROOT / "docs/sprint2/family_p/P2P3_objectives_harm.md").read_text()
    candidate_registry = json.loads((ROOT / "docs/sprint2/candidates.json").read_text())
    p3_registry = candidate_registry["P3"]["track_E"]
    for label, text, needles in (
        ("P3 narrative", p3doc, ("+14.0 to +669.5", "+738.4")),
        ("P3 candidate registry", p3_registry, ("+14.0 to +669.5", "+738.4")),
    ):
        p3_claim_cells += len(needles)
        for needle in needles:
            if needle not in text:
                p3_claim_mismatches.append(f"{label} missing scoped claim {needle!r}")
    p3_dev = p1[p1["policy"].isin(["P3_follow", "A5b"])].pivot(
        index=["regime", "seed"], columns="policy", values="net")
    dev_delta = (p3_dev["P3_follow"] - p3_dev["A5b"]).groupby(level="regime").mean()
    p3_claim_cells += 2
    if not (np.isclose(round(float(dev_delta.min()), 1), 37.2)
            and np.isclose(round(float(dev_delta.max()), 1), 163.0)):
        p3_claim_mismatches.append(
            f"P3 dev paired J range: {dev_delta.min():.1f}..{dev_delta.max():.1f} != +37.2..+163.0")
    if "+37.2 to +163.0" not in p3_registry:
        p3_claim_mismatches.append("P3 registry omits recomputed 23-regime/20-seed dev contrast range")
    p3_ledger = next(r for r in json.loads(
        (ROOT / "docs/sprint2/family_p/ledger.json").read_text()) if r["id"] == "P3")
    if "+37.2 to +163.0" not in p3_ledger["track_E"]:
        p3_claim_mismatches.append("P3 family ledger omits recomputed dev contrast range")
    checks.append(report_check("P3 narrative and registry scope", p3_claim_mismatches,
                               p3_claim_cells))

    result = {"audit": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
              "checks": checks,
              "limitations": ["Does not reproduce every P3/P6 narrative claim or every family-level narrative in the P-family documents.",
                              "Numerical agreement does not establish theorem validity, causal interpretation, or independent confirmation."]}
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["audit"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
