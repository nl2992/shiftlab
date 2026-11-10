"""Generate docs/paper1_scale25/10_25_DATASET_RESULTS.md and the C1 section of 08 from validated outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
R = ROOT / "docs/paper1_scale25/confirm_C1_results"
S = json.loads((R / "summary.json").read_text())
REG = json.loads((ROOT / "docs/paper1_scale25/confirm_registration_C1.json").read_text())
PD = pd.read_csv(R / "per_dataset.csv")
PP = pd.read_csv(R / "panel_pooled.csv")
GQ = pd.read_csv(R / "panel_geq_sota.csv")
BY = pd.read_csv(R / "by_domain.csv")
DEC = pd.read_csv(R / "decomposition.csv")
DEV = pd.read_csv(ROOT / "docs/paper1_scale25/c1_dev_eval.csv")
P, PO = S["primary"], S["primary_org_merged"]
C = S["certify_cohort"]["counts"]


def f(x, n=3):
    return f"{x:.{n}f}"


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.tolist()) + " |")
    return "\n".join(out)


# eligibility table
el = []
for d in REG["datasets"]:
    e = d["eligibility"]
    v = e.get("validation", {})
    el.append(
        {
            "#": d["protocol_order"],
            "dataset": d["name"],
            "window": f"{d['window'][0]}..{d['window'][1]}",
            "n_after_filter": d.get("n_after_filter", ""),
            "episodes": d.get("episodes", ""),
            "delay": d.get("delay", ""),
            "val disagreement": f(v["disagreement"]) if v else "",
            "val err inc/chal": f"{f(v['err_incumbent'])}/{f(v['err_challenger'])}" if v else "",
            "eligible": "yes" if e["eligible"] else "NO: " + e.get("reason", ""),
            "ledger idx": d.get("ledger_index", ""),
        }
    )
ELT = md(pd.DataFrame(el))

pdt = PD[
    ["protocol_order", "ledger_index", "dataset", "domain", "episodes", "J_v1", "J_Wcut",
     "r_v1_vs_Wcut_pct", "dL_pp", "alpha_i", "L_lower_pct", "labels_v1", "labels_W",
     "switches_v1", "switches_W"]
].copy()  # fmt: skip
pdt["alpha_i"] = pdt.alpha_i.map(lambda v: f"{v:.2e}")
for c in pdt.columns:
    if pdt[c].dtype == float and c != "alpha_i":
        pdt[c] = pdt[c].map(lambda v: f"{v:.3f}")
pdt.columns = ["#", "idx", "dataset", "domain", "eps", "J v1", "J W+cut", "r %", "dL pp", "alpha_i",
               "L % (primary_lower)", "labels v1", "labels W+cut", "sw v1", "sw W+cut"]  # fmt: skip

sec = S["secondary"]
sec_t = pd.DataFrame(
    [
        {"contrast": k, "K": v["K"], "mean r %": f(v["mean"]), "95% t-CI": f"[{f(v['lo'])}, {f(v['hi'])}]",
         "p (one-sided)": f"{v['p']:.2e}", "Holm p": f"{v['p_holm']:.2e}", "r>0 / r<0": f"{v['n_pos']} / {v['n_neg']}",
         "mean dL pp": f(v["mean_dL_pp"])}
        for k, v in sec.items()
    ]
)  # fmt: skip


def panel_tab(sets):
    q = PP[PP.set.isin(sets)].copy()
    q = q.sort_values("mean_r_pct")
    return md(pd.DataFrame({"comparator": q.comp, "mean r % (v1 better if >0)": q.mean_r_pct.map(f),
                            "95% t-CI": [f"[{a:.3f}, {b:.3f}]" for a, b in zip(q.ci_lo, q.ci_hi, strict=True)],
                            "r>0": q.n_pos, "r<0": q.n_neg}))  # fmt: skip


gq = S["geq_sota_counts"]
bo = S["best_of_panel"]
dev_r = DEV.r_v1_vs_Wcut_pct
dec = DEC.copy()
for c in dec.columns[1:]:
    dec[c] = dec[c].map(lambda v: f"{v:.2f}")
bd = BY.copy()
for c in ("mean_r", "mean_dL"):
    bd[c] = bd[c].map(f)
nz = PD[PD.r_v1_vs_Wcut_pct != 0]
from scipy import stats as st

tz = st.ttest_1samp(nz.r_v1_vs_Wcut_pct, 0, alternative="greater")
best_counts = pd.Series(bo["best_policy"]).value_counts()
neg_ds = PD[PD.r_v1_vs_Wcut_pct < 0].dataset.tolist()

DOC = f"""# 10 - Paper 1 scale-25: C1 confirmation (frozen v1 on a 21-dataset cohort)

**Honest title.** This is the C1 confirmation of the frozen v1 package on **{P["K"]} eligible datasets**, not a 25-dataset
result. 22 datasets were registered in `07a`; one failed a C4 gate and is reported, not replaced. All numbers below are
produced by `scripts/paper1_scale25/confirm_c1_analyze.py` from `docs/paper1_scale25/confirm_C1_results/`.

## 1. Provenance

- Protocol: `07a_PROTOCOL_C1_V1_22.md` (locked at `607a7eea`, before any confirmation build). Registration:
  `confirm_registration_C1.json` and ledger rows 8-28, committed at `af2d76a9` before any policy ran on these windows.
- Builds: `scripts/paper1_scale25/data/confirm_build.py` (wraps `c4_build.build`, unchanged gates; records only validation
  statistics). Records in `confirm_builds/`; sealed arrays in `data/scale25_confirm/` (gitignored, checksums in the registration).
- Run: `scripts/paper1_scale25/confirm/c1_run.py` via `c1_watch.py` (detached, resumable), seed base 2026111001, 10 policy seeds, all
  episodes, 62 policies per (dataset, episode, seed); code SHA `af2d76a9` (clean). The runner was first smoke-tested to reproduce
  the stored fresh sf_311 records bit-exactly for all 30 stored policies (incl. v1, W+cut, W+pair, 25 panel) on 2 episodes x 3 seeds.
  Record-file hashes: `confirm_C1_results/records_sha256.txt` (the records themselves, 409 MB, are not in Git).
- Analysis: single pass, `confirm_C1_results/summary.json`. Commands:
  `python scripts/paper1_scale25/data/run_confirm_builds.py`, `python scripts/paper1_scale25/confirm/confirm_register.py`,
  `python scripts/paper1_scale25/confirm/c1_watch.py -- --reg docs/paper1_scale25/confirm_registration_C1.json --out outputs/paper1_scale25/c1/run --parts core,panel,cut,ports --workers 18`,
  `python scripts/paper1_scale25/confirm_c1_analyze.py --records-dir outputs/paper1_scale25/c1/run --open-ledger`.

## 2. Eligibility (C4 gates, validation statistics only)

{ELT}

Ineligible: **capitalbikeshare_dc** (validation disagreement below the .03 gate). It is not repaired or replaced and holds no ledger
index. Notes: `epa_aqi_county` is truncated by publication (last event 2026-05-31) and has delay 1000; `ghcn_us_rain` has delay 1000;
`montgomery_police_dispatch` has 38 episodes (just above the 35 gate).

**Cutoff degeneracy (a protocol consequence, not a tuning choice).** For delay 1000 the frozen cutoff (no purchase when
`t + delay > T - 1100`) is closed for the entire 2000-event episode. On `epa_aqi_county` and `ghcn_us_rain` every cutoff arm buys zero
labels and never switches, so v1 = W+cut exactly (r = 0, L = 0). These two datasets carry no information about the method and enter
the primary mean as zeros, as the protocol fixed.

## 3. Pre-opening development evaluation (07a section 3; descriptive)

Core arms on the DEV windows of the 12 new sources (`c1_dev_eval.csv`, seed base 2026111000): mean r (v1 vs W+cut) = {f(dev_r.mean())} %,
{int((dev_r > 0).sum())} positive / {int((dev_r < 0).sum())} negative / {int((dev_r == 0).sum())} zero. The matching confirmation results are in the per-dataset table below. No dataset was added, dropped or reordered on this basis.

## 4. Primary result (design A2, one test)

H0: mean r_d <= 0 over the {P["K"]} eligible datasets; reference W+cut; r_d = 100 (J_W+cut - J_v1) / J_W+cut.

| quantity | value |
|---|---|
| equal-dataset mean r | **{f(P["mean"])} %** |
| 95% t-CI | [{f(P["lo"])}, {f(P["hi"])}] |
| one-sided t-test | t = {f(P["t"], 2)}, **p = {P["p"]:.2e}** (K = {P["K"]}) |
| sign count | {P["n_pos"]} positive, {P["n_neg"]} negative, {P["n_zero"]} exactly zero |
| mean dJ (pp of T) | {f(P["dJ_pp_mean"], 4)} |
| mean dL/T (pp) | {f(P["mean_dL_pp"], 4)} (constraint <= +0.1: {"met" if P["accuracy_constraint_dL_le_0.1pp"] else "NOT met"}) |
| verdict by the 07a rule | **{"passes" if P["passes"] else "does not pass"}** |

Organisation-merged sensitivity (pairs {{nyc_ems, nyc_fire}}, {{divvy, capitalbikeshare}} [only divvy eligible], {{mc311_montgomery, montgomery_police_dispatch}} averaged first): K = {PO["K"]},
mean r = {f(PO["mean"])} % [{f(PO["lo"])}, {f(PO["hi"])}], p = {PO["p"]:.2e}.

Post-hoc descriptive (not a protocol test): excluding the two degenerate delay-1000 datasets, K = {len(nz)}, mean r = {f(nz.r_v1_vs_Wcut_pct.mean())} %, t-test p = {tz.pvalue:.2e}.

**Size.** The effect is statistically clear but small: v1 saves {f(P["mean"], 2)} % of W+cut's net cost on average (about {f(-P["dJ_pp_mean"], 3)} pp of T). By the
programme's grading (substantial >= 2 %, meaningful >= 0.5 %, small otherwise) this is **small**. It is far below the 2.5 % per-dataset
target of the scale-25 programme.

## 5. Per-dataset certification (design B, union bound; ledger rows opened)

Ledger validation problems: {S["ledger_problems"] or "none"}.

| counter | value |
|---|---|
| registered (incl. 7 legacy) | {C["registered"]} |
| legacy reserved | {C["legacy_reserved"]} |
| opened (this cohort) | {C["opened"]} |
| positive point estimate (r_hat > 0) | {C["positive_r"]} |
| supported (L > 0) | **{C["supported_L_gt_0"]}** |
| selected | {C["selected"]} |

`certify_cohort` (target |S| >= 25, mean L >= 2.5): **success = {S["certify_cohort"]["success"]}**. All-opened mean r_hat = {f(S["certify_cohort"]["all_opened_mean_r_hat"])} %;
cross-dataset t95 interval [{f(S["certify_cohort"]["all_opened_mean_cross_dataset_t95"][0])}, {f(S["certify_cohort"]["all_opened_mean_cross_dataset_t95"][1])}]; simultaneous lower bound of the all-opened mean: -inf
(some per-dataset L are -inf). As predicted in 09, the registered target is not reachable with K <= 22, and in addition no individual
dataset has a positive union-bound lower bound at alpha_i = .05/(i(i+1)) with i = 8..28. The population-level mean is positive; the
per-dataset effect sizes are too small to certify one by one.

## 6. Secondary contrasts (Holm over the two)

{md(sec_t)}

W+pair vs W+cut and v1 vs EQ+cut are both positive, and the two pair variants give similar mean r (W+pair minus v1: {f(S["secondary"]["Wpair_vs_Wcut"]["mean"] - P["mean"])} % points; not tested). The cohort result is therefore a property of the E48+F60 add-on, not of a particular parent.

## 7. Per-dataset results (registration order)

{md(pdt)}

Negative r: {", ".join(neg_ds)}.

By domain (mean of per-dataset r, v1 vs W+cut):

{md(bd)}

## 8. Descriptive panel comparisons (v1 vs each comparator)

r = 100 (J_comp - J_v1) / J_comp, positive favours v1; pooled over datasets with t-CIs. The >= SOTA rule is the amendment-11 rule (v1 non-inferior
within 1 % of the comparator's cost, episode-bootstrap one-sided 95 %, against every comparator in the set). Raw and cutoff-equipped panels are
reported separately.

**>= SOTA counts (of {P["K"]} datasets):** raw 25 comparators: **{gq["raw25"]}**; arm R alone: {gq["armR"]}; cutoff-equipped 25 (24 wrapped + unwrapped model_selector_causal): **{gq["cut25"]}**;
both: {gq["raw25_and_cut25"]}; paper-formula ports raw: {gq["ports_raw"]}, with cutoff: {gq["ports_cut"]}.
Datasets failing the raw panel: {", ".join(GQ[(GQ.set == "raw25") & ~GQ.noninf_all].stream)}. Failing the cutoff-equipped panel: {", ".join(GQ[(GQ.set == "cut25") & ~GQ.noninf_all].stream)}.

### Raw panel (25 + arm R)
{panel_tab(["raw25", "armR"])}

### Cutoff-equipped panel (H = 1100; model_selector_causal unwrapped)
{panel_tab(["cut25"])}

### Paper-formula ports (Model Picker, CAMS), raw and with cutoff
{panel_tab(["ports_raw", "ports_cut"])}

(`mp_paper_sample` acts by sampling the model each step and is cost-infeasible under c_s = 5, as found in 05. `han_arw_label_clock` is a weak adapter.)

**Best-of-panel (OPTIMISTIC: the per-dataset best policy among all 60 panel, control and port policies is chosen after seeing these results).**
v1 vs that reference: mean r = {f(bo["mean"])} % [{f(bo["lo"])}, {f(bo["hi"])}]; v1 better on {bo["n_pos"]}, worse on {bo["n_neg"]} datasets. The most frequent best policy is
{best_counts.index[0]} ({best_counts.iloc[0]} datasets), a cutoff-equipped economic-rule control (`econF_mo5_*_H1100`): v1 does not beat the best cutoff-equipped control.
This is the honest limit on the novelty claim: the cohort win is against the matched cutoff reference W+cut and against nearly all raw adapters, but a tuned economic-rule control
equipped with the same cutoff is as good or slightly better (pooled r vs `econF_mo5_m5_H1100` = {f(PP[PP.comp == "econF_mo5_m5_H1100"].mean_r_pct.iloc[0])} %, CI includes 0).

## 9. Labels, switches, decomposition

Equal-dataset means per episode (net, loss in cost units per 2000 events):

{md(dec)}

v1 buys {f(DEC.labels[0], 1)} labels per episode against {f(DEC.labels[1], 1)} for W+cut ({f(100 * (1 - DEC.labels[0] / DEC.labels[1]), 0)} % fewer) with a similar loss and a slightly lower switch count: the gain
is label spend and reversal churn, not accuracy (mean dL/T = {f(P["mean_dL_pp"], 3)} pp).

## 10. Caveats

- K = {P["K"]}, not 22 or 25; two datasets (epa, ghcn) are degenerate by the delay-1000/cutoff interaction; {int(BY[BY.domain == "municipal-311"].K.iloc[0])} of the {P["K"]} are municipal-311 streams (the organisation-merged sensitivity gives a similar mean).
- Per-dataset certification is not achieved on any dataset; the cohort claim is a population-mean claim with t-based inference across datasets (independence across datasets is assumed; same-operator or same-city pairs are addressed only by the merged sensitivity).
- Reference choice: W+cut was locked as primary. Against the best cutoff-equipped control the result is negative (best-of-panel, optimistic).
- The cutoff-equipped panel uses a single H = 1100 for every comparator, not per-family tuned values; `model_selector_causal` is unwrapped; author-code parity (T1) for the ports is not established (05).
- epa_aqi_county window ends 2026-05-31 by publication; baltimore (4 months), bts (2 months), dc and sandiego (half-year) windows are as specified.
- Smoke/dev checks (runner parity, dev evaluation) are not confirmatory; only sections 4-6 are confirmatory evidence.

## 11. Continue / pivot / stop

- **Confirmed (small):** the frozen v1 beats its matched W+cut reference on the pre-registered cohort (mean r = {f(P["mean"])} %, p = {P["p"]:.1e}, {P["n_pos"]}/{P["K"]} datasets positive, accuracy constraint met).
- **Not achieved:** the 2.5 % certified-reduction target (0 of {C["opened"]} datasets with L > 0; cohort certificate false) and superiority over the best cutoff-equipped control.
- **Assessment: pivot the claim, continue the programme.** Report v1 as a small, statistically reliable cost-trimming add-on (label spend), not as a state-of-the-art monitoring result with a certified 2.5 % gain. Further gains need a different lever
  (information source or acquisition) rather than more tuning of this package; the ceiling visible in the best-of-panel table is the economic-rule family with a cutoff.
"""

(ROOT / "docs/paper1_scale25/10_25_DATASET_RESULTS.md").write_text(DOC, encoding="utf-8")

LEDGER_SEC = f"""

## 4. C1 confirmation ledger entries (2026-11-10)

Protocol `07a_PROTOCOL_C1_V1_22.md` (id `P1-SCALE25-C1-V1-22`), contrast v1 vs W+cut. Registered before any policy run at `af2d76a9`
(`confirm_registration_C1.json`); 21 eligible datasets took indices 8..28 in protocol order (index 19 of the protocol order,
capitalbikeshare_dc, failed the C4 disagreement gate and holds no index; it is not replaced). All 21 were opened in one analysis pass
(`confirm_c1_analyze.py --open-ledger`, results commit following `af2d76a9`). Chain validation after opening: {S["ledger_problems"] or "no problems"}.

Counters (never merged): registered {C["registered"]} (7 legacy), opened in C1 {C["opened"]}, positive point estimate {C["positive_r"]}, supported (L > 0) {C["supported_L_gt_0"]}, selected {C["selected"]}.
`certify_cohort(min_datasets=25, min_R=2.5)`: success = {S["certify_cohort"]["success"]}. All-opened mean r_hat = {f(S["certify_cohort"]["all_opened_mean_r_hat"])} %.
Per-dataset r_hat, alpha_i and L are in `confirm_C1_results/per_dataset.csv`; full discussion in `10_25_DATASET_RESULTS.md`.
"""
p8 = ROOT / "docs/paper1_scale25/08_CONFIRMATION_LEDGER.md"
t = p8.read_text(encoding="utf-8")
if "## 4. C1 confirmation ledger entries" not in t:
    p8.write_text(t.rstrip("\n") + LEDGER_SEC, encoding="utf-8")
print("ok")
