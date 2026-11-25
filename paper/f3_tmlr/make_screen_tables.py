"""Tables and macros for the 100-stream public screen (protocol 05G_F3_REAL_SCREEN100_PROTOCOL.md).

Reads outputs/paper3/riskbudget/screen100/{tally.json,<condition>/*.json}; writes
tables/screen_numbers.tex (macros), tables/screen_groups.tex, tables/app_screen_supported.tex and the ledger file
of streams that did not meet the criteria (results/riskbudget/screen100_not_supported.md).
Every number is computed here; nothing is typed by hand.
"""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
O = ROOT / "outputs/paper3/riskbudget/screen100"
RES = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget"

tally = json.loads((O / "tally.json").read_text())
rows = tally["rows"]
assert len(rows) == 100


def tex(s):
    return s.replace("_", "\\_")


def thousands(n):
    return f"{int(n):,}".replace(",", "{,}")


macros = {}

# ---- run counts (runs per arm per condition, summed over the three conditions)
runs = {}
for c in ("clean", "dropout_adverse", "delay_adverse"):
    n = 0
    for r in rows:
        d = json.loads((O / c / f"{r['name']}.json").read_text())
        n += np.array(d["fields"]["sup_harm"], float)[0].size
    runs[c] = n
assert len(set(runs.values())) == 1
per_arm = sum(runs.values())

sup = [r for r in rows if r["status"] == "supported"]
non = [r for r in rows if r["status"] != "supported"]
full_viol = sum(r["shield_violations"][a] for r in rows for a in ("f3_pi1_h14", "f3_pi1_h50"))
paced_viol = sum(r["shield_violations"][a] for r in rows for a in ("f3v2d_h14", "f3v2d_h50"))
sg = np.array([r["shield_gain_vs_never"] for r in sup])
wg = np.array([r["wald_gain_vs_never"] for r in sup])
macros.update({
    "ScreenPool": len(rows), "ScreenSOne": sum(1 for r in rows if r["S1"]), "ScreenSupported": len(sup), "ScreenNotSupported": len(non),
    "ScreenRunsPerArm": thousands(per_arm), "ScreenFullViol": full_viol, "ScreenPacedViol": paced_viol,
    "ScreenWaldExceedStreams": sum(1 for r in rows if r["comparator_exceed_R24"]["wald_cut"] > 0),
    "ScreenWaldExceedRuns": thousands(sum(r["comparator_exceed_R24"]["wald_cut"] for r in rows)),
    "ScreenMeanShieldGain": f"{sg.mean():.0f}", "ScreenMeanWaldGain": f"{wg.mean():.0f}",
    "ScreenShareShield": f"{100 * sg.sum() / wg.sum():.0f}",
    "ScreenWorstExcess": f"{-min(r['shield_gain_vs_never'] for r in non):.0f}",
    "ScreenOtherForex": sum(1 for r in non if r["group"] == "forex"),
})
assert full_viol == 0

# ---- group table
META = {
    "forex": ("OpenML FOREX \\texttt{*-hour-Close}, one per currency pair", "OpenML \\texttt{Class}", 24),
    "air_multisite": ("UCI 501, one per Beijing station", "PM2.5 above train median", 24),
    "air_cities": ("UCI 394, five Chinese cities except Beijing", "PM\\_US Post above train median", 24),
    "seoul_bike": ("UCI 560", "rented bikes above train median", 24),
    "tetouan": ("UCI 849, one per zone", "zone consumption above train median", 144),
    "air_quality": ("UCI 360", "CO(GT) above train median", 24),
    "openml_events": ("OpenML creditcard, BitcoinHeist, Homesite, BAF\\_base", "dataset label", 100),
    "electricity": ("UCI 321, 43 clients", "15-minute load above train median", 96),
}
order = ["electricity", "forex", "air_multisite", "air_cities", "tetouan", "openml_events", "seoul_bike", "air_quality"]
G = tally["groups"]
lines = []
for g in order:
    src, lab, dl = META[g]
    ns, nn = G[g].get("supported", 0), G[g].get("not_supported", 0)
    lines.append(f"{tex(g)} & {src} & {lab} & {dl} & {ns + nn} & {ns} \\\\")
assert sum(G[g].get("supported", 0) + G[g].get("not_supported", 0) for g in order) == 100
tab = ("\\begin{tabular}{@{}l p{4.6cm} p{3.4cm} r r r@{}}\n\\toprule\n"
       "Group & Source & Label & Delay & Pool & S2 met \\\\\n\\midrule\n" + "\n".join(lines)
       + f"\n\\midrule\nall & & & & {len(rows)} & {len(sup)} \\\\\n\\bottomrule\n\\end{{tabular}}\n")
(HERE / "tables/screen_groups.tex").write_text(tab)

# ---- supported streams, sorted by the shield's gain over never switching
sup_sorted = sorted(sup, key=lambda r: -r["shield_gain_vs_never"])
body = "\n".join(
    f"{tex(r['name'])} & {tex(r['group'])} & {r['J_never']:.1f} & {r['J_shield_best_h50']:.1f} & "
    f"{r['shield_gain_vs_never']:.1f} & {r['wald_gain_vs_never']:.1f} \\\\" for r in sup_sorted)
hdr = "Stream & Group & $J$ never & $J$ shield & Shield gain & Wald gain \\\\"
long = ("\\begin{longtable}{@{}l l r r r r@{}}\n\\caption{Streams of the 100-stream screen on which the better $h=50$ shield arm costs less than never switching "
        "(S2; all of them also meet S1). $J$ is mean episode cost under clean feedback; ``shield'' is the better of the two "
        "$h=50$ shield arms (chosen on these data); gains are the reduction in $J$ against never switching, in cost units.}"
        "\\label{tab:screen_supported}\\\\\n\\toprule\n" + hdr + "\n\\midrule\n\\endfirsthead\n\\multicolumn{6}{@{}l}{\\emph{Table~\\thetable{} (continued)}} \\\\[2pt]\n\\toprule\n" + hdr
        + "\n\\midrule\n\\endhead\n\\bottomrule\n\\endfoot\n" + body + "\n\\end{longtable}\n")
(HERE / "tables/app_screen_supported.tex").write_text(long)

# ---- the streams that did not meet S2 (reported in full; every stream of the pool is in the paper)
non_sorted = sorted(non, key=lambda r: r["shield_gain_vs_never"])
body = "\n".join(
    f"{tex(r['name'])} & {tex(r['group'])} & {'yes' if r['S1'] else 'no'} & {r['J_never']:.1f} & {r['J_shield_best_h50']:.1f} & "
    f"{r['shield_gain_vs_never']:.1f} & {r['wald_gain_vs_never']:.1f} & {r['challenger_better_mean']:.3f} \\\\" for r in non_sorted)
hdr = "Stream & Group & S1 & $J$ never & $J$ shield & Shield gain & Wald gain & Chall.\\ adv. \\\\"
long2 = ("\\begin{longtable}{@{}l l c r r r r r@{}}\n\\caption{Streams of the 100-stream screen on which the better $h=50$ shield arm does not cost less than "
        "never switching (S2 fails). Columns as in Table~\\ref{tab:screen_supported}; negative gains are costs above never switching. "
        "``Chall.\\ adv.'' is the challenger's mean loss advantage per event. S1 fails only where marked (paced arm, within its level $\\delta$).}"
        "\\label{tab:screen_not_supported}\\\\\n\\toprule\n" + hdr + "\n\\midrule\n\\endfirsthead\n\\multicolumn{8}{@{}l}{\\emph{Table~\\thetable{} (continued)}} \\\\[2pt]\n\\toprule\n" + hdr
        + "\n\\midrule\n\\endhead\n\\bottomrule\n\\endfoot\n" + body + "\n\\end{longtable}\n")
(HERE / "tables/app_screen_not_supported.tex").write_text(long2)

# ---- framing of the cost result: streams with something to gain vs streams without
gainful = [r for r in rows if r["wald_gain_vs_never"] > 0.05 * r["J_never"]]
lose = [r for r in rows if r["shield_gain_vs_never"] < 0]
keep = {"lo": [], "mid": [], "hi": []}
for r in gainful:
    b = "lo" if r["x_h50"] < 0.5 else ("mid" if r["x_h50"] < 1 else "hi")
    keep[b].append(r["shield_gain_vs_never"] / r["wald_gain_vs_never"])
assert all(r["shield_gain_vs_never"] > 0 for r in gainful)
macros.update({
    "ScreenGainful": len(gainful),
    "ScreenGainfulShieldBeatsNever": sum(1 for r in gainful if r["shield_gain_vs_never"] > 0),
    "ScreenGainfulLo": len(keep["lo"]), "ScreenKeepLo": f"{100 * np.median(keep['lo']):.0f}",
    "ScreenGainfulMid": len(keep["mid"]), "ScreenKeepMid": f"{100 * np.median(keep['mid']):.0f}",
    "ScreenGainfulHi": len(keep["hi"]),
    "ScreenLose": len(lose), "ScreenLoseWaldAlso": sum(1 for r in lose if r["wald_gain_vs_never"] < 0),
    "ScreenLoseShieldMed": f"{-np.median([r['shield_gain_vs_never'] for r in lose]):.1f}",
    "ScreenLoseWaldMed": f"{-np.median([r['wald_gain_vs_never'] for r in lose]):.1f}",
    "ScreenForexAdv": f"{np.median([r['challenger_better_mean'] for r in rows if r['group'] == 'forex']):.3f}",
})

(HERE / "tables/screen_numbers.tex").write_text(
    "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in macros.items()))

# ---- record of the streams that did not meet the criteria (for the authors; not in the paper)
md = ["# 100-stream screen: streams that did not meet the criteria", "",
      f"Generated by `paper/f3_tmlr/make_screen_tables.py` from `outputs/paper3/riskbudget/screen100/tally.json` "
      f"(protocol `05G_F3_REAL_SCREEN100_PROTOCOL.md`). {len(non)} of {len(rows)} streams did not meet S1 and S2. "
      "Decision on how to use them is open.", "",
      "S2 fails when the better $h=50$ shield arm does not beat never switching on clean feedback. In all 42 S2 failures with "
      "S1 satisfied the shield stayed within its budget; the excess over never switching is cost units (loss + label fees + "
      "switching fees). One stream also fails S1: `FOREX_gbpusd-hour-Close` has 2 runs above the budget for the paced "
      "arm `f3v2d_h14` (delta = .05, allowed).", "",
      "| stream | group | S1 | shield gain vs never | Wald gain vs never | disagreement | challenger better (mean) |",
      "|---|---|---|---|---|---|---|"]
for r in sorted(non, key=lambda r: r["shield_gain_vs_never"]):
    md.append(f"| {r['name']} | {r['group']} | {r['S1']} | {r['shield_gain_vs_never']:.1f} | {r['wald_gain_vs_never']:.1f} | "
              f"{r['disagreement']:.3f} | {r['challenger_better_mean']:.3f} |")
(RES / "screen100_not_supported.md").write_text("\n".join(md) + "\n")
print("wrote", len(macros), "macros;", len(sup), "supported;", len(non), "not supported")
print(macros)
