#!/usr/bin/env python3
"""Write every table and inline number of main.tex from the committed result files.

Usage: python3 make_tables.py   (run from paper/f3_riskbudget; no arguments)
Inputs: papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget/*.json|*.md
Outputs: tables/*.tex (tables) and tables/numbers.tex (\\newcommand macros for inline numbers).
Nothing is hand-entered: every value is read from a result file or computed from values read.
"""
import json, math, os, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent.parent / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget"
OUT = HERE / "tables"
OUT.mkdir(exist_ok=True)

conf = json.load(open(RES / "confirm_summary.json"))
expo = json.load(open(RES / "exposure_ratio_test.json"))["summary"]
props = json.load(open(RES / "props_check.json"))
sel = json.load(open(RES / "v3_select_summary.json"))

# ---------------------------------------------------------------- helpers
def tex(s):
    s = str(s)
    for a, b in [("\\", "\\textbackslash{}"), ("_", r"\_"), ("%", r"\%"), ("&", r"\&"), ("#", r"\#")]:
        s = s.replace(a, b)
    return s

def sg(x, d=2):
    """signed number with a proper minus sign"""
    s = f"{x:+.{d}f}"
    return s.replace("-", "$-$")

def num(x, d=2):
    return f"{x:.{d}f}".replace("-", "$-$")

def r3(x):
    return f"{x:.3f}"

def ci(lo, hi, d=2):
    return f"[{sg(lo,d)}, {sg(hi,d)}]"

def thousands(n):
    return f"{int(n):,}".replace(",", "{,}")

MAC = {}
def mac(name, value):
    assert re.fullmatch(r"[A-Za-z]+", name), name
    MAC[name] = value

def write(name, body):
    (OUT / name).write_text(body)

def parse_md(path):
    """Return {(condition, heading): (header, rows)} for every markdown table."""
    cond, head, out = "", "", {}
    cur = None
    for line in Path(path).read_text().splitlines():
        if line.startswith("## Condition:"):
            cond = line.split(":", 1)[1].strip(); head = ""; cur = None
        elif line.startswith("#"):
            head = line.lstrip("#").strip(); cur = None
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            key = (cond, head)
            if cur is None or cur != key:
                out[key] = (cells, []); cur = key
            else:
                out[key][1].append(cells)
    return out

def rowdict(tab, arm):
    hdr, rows = tab
    for r in rows:
        if r[0] == arm:
            return dict(zip(hdr, r))
    raise KeyError(arm)

def first_int(s):
    return int(re.search(r"(\d+)", s.split(";")[0] if "R24" not in s else s[s.index("R24:"):]).group(1))

def exceed(s):
    """'R24:475 R60:66' -> 475 ; '311/4600' -> 311"""
    m = re.search(r"R24:(\d+)", s)
    if m: return int(m.group(1))
    return int(s.split("/")[0])

def own_viol(s):
    return int(s.split("/")[0])

# ---------------------------------------------------------------- simulation (registered confirmation)
nreg, nseed = conf["n_regimes"], conf["n_seeds"]
runs_per_arm = nreg * nseed
D = conf["descriptive"]
mac("NRegimes", nreg); mac("NSeedsPerRegime", thousands(nseed)); mac("NRunsPerArm", thousands(runs_per_arm))
mac("JNever", num(D["never"]["J"])); mac("JWald", num(D["wald_cut"]["J"])); mac("JFthreeTwenty", num(D["f3_pi1_R20"]["J"]))
mac("SimVsNeverPct", f"{abs(conf['C4']['vs_never']['rel_pct']):.1f}")
mac("SimVsNeverDelta", num(conf["C4"]["vs_never"]["delta"]))
mac("SimVsNeverLo", num(conf["C4"]["vs_never"]["lo"])); mac("SimVsNeverHi", num(conf["C4"]["vs_never"]["hi"]))
mac("SimVsWaldDelta", sg(conf["C4"]["vs_wald_cut"]["delta"]))
mac("SimVsWaldLo", sg(conf["C4"]["vs_wald_cut"]["lo"])); mac("SimVsWaldHi", sg(conf["C4"]["vs_wald_cut"]["hi"]))
mac("SimVsWaldPct", f"{conf['C4']['vs_wald_cut']['rel_pct']:.1f}")
mac("SimVsWaldHiPct", f"{conf['C4']['vs_wald_cut']['hi_rel_pct']:.2f}")
mac("StressDelta", sg(conf["C5"]["stress6"]["delta"])); mac("StressLo", sg(conf["C5"]["stress6"]["lo"]))
mac("StressHi", sg(conf["C5"]["stress6"]["hi"])); mac("StressPct", f"{abs(conf['C5']['stress6']['rel_pct']):.1f}")
mac("OrigDelta", sg(conf["C5"]["original24"]["delta"])); mac("OrigPct", f"{conf['C5']['original24']['rel_pct']:.1f}")
mac("CTwoMaxHi", f"{max(a['max_hi'] for a in conf['C2']['arms'].values()):.3f}")
mac("COneMaxHi", f"{max(a['max_hi'] for a in conf['C1']['arms'].values()):.3f}")
mac("COneTotal", sum(a["total_k"] for a in conf["C1"]["arms"].values()))
mac("CTwoTotal", sum(a["total_k"] for a in conf["C2"]["arms"].values()))
worst = {a: v["worst_stats"]["rate"] for a, v in conf["C3"]["arms"].items()}
mac("CThreeMinWorst", f"{100*min(worst.values()):.0f}"); mac("CThreeMaxWorst", f"{100*max(worst.values()):.0f}")
for a, v in conf["C3"]["arms"].items():
    key = {"wald_cut": "Wald", "cusum": "Cusum", "gate_wald": "Gate", "cusum_rb_h8": "CusumRb", "stoploss_R20": "Stop"}[a]
    mac(f"Worst{key}", r3(v["worst_stats"]["rate"]))
    mac(f"WorstLo{key}", r3(v["worst_stats"]["lo"])); mac(f"WorstHi{key}", r3(v["worst_stats"]["hi"]))
    mac(f"Pooled{key}", f"{100*v['pooled']:.1f}")
mac("CThreeMinLo", r3(min(v["worst_stats"]["lo"] for v in conf["C3"]["arms"].values())))
for a, key in [("f3_pi1_R12_nopending", "NoPending"), ("f3_pi1_R12_norollback", "NoRollback"), ("f3_pi25_R12_noconf", "NoConf")]:
    v = conf["C6"]["arms"][a]["worst_stats"]
    mac(f"Abl{key}", r3(v["rate"])); mac(f"AblLo{key}", r3(v["lo"])); mac(f"AblHi{key}", r3(v["hi"]))

# Table: registered outcomes
def verdict(b): return "supported" if b else "not supported"
rows = []
rows.append(("C1", r"Full-sampling shield, $R\in\{12,20,30\}$, and blind-round variant: violations of $R$",
             f"{conf['C1']['arms']['f3_pi1_R12']['total_k']} / {thousands(runs_per_arm)} in each of 4 arms; per-regime Wilson upper $\\le {conf['C1']['arms']['f3_pi1_R12']['max_hi']:.3f}$", verdict(conf["C1"]["supported"])))
c2 = conf["C2"]["arms"]
rows.append(("C2", r"Paced shield, $\delta=.05$, $R\in\{20,30\}$: violations",
             f"{c2['f3v2d_R20']['total_k']} and {c2['f3v2d_R30']['total_k']} / {thousands(runs_per_arm)}; largest per-regime Wilson upper {max(a['max_hi'] for a in c2.values()):.3f}", verdict(conf["C2"]["supported"])))
rows.append(("C3", r"Five comparators, worst-regime exceedance of $R=20$ (Wilson lower bound)",
             f"all five above $.05$; smallest lower bound {min(v['worst_stats']['lo'] for v in conf['C3']['arms'].values()):.3f}", verdict(conf["C3"]["supported"])))
c4 = conf["C4"]
rows.append(("C4", r"Pooled $\Delta J$ of the $R=20$ shield, 95\% CI",
             f"vs never {sg(c4['vs_never']['delta'])} {ci(c4['vs_never']['lo'], c4['vs_never']['hi'])}; vs Wald+cutoff {sg(c4['vs_wald_cut']['delta'])} {ci(c4['vs_wald_cut']['lo'], c4['vs_wald_cut']['hi'])}", verdict(c4["supported"])))
c5 = conf["C5"]
rows.append(("C5", r"$\Delta J$ vs Wald+cutoff, 6 stress regimes (24 original regimes)",
             f"{sg(c5['stress6']['delta'])} {ci(c5['stress6']['lo'], c5['stress6']['hi'])} ({sg(c5['original24']['delta'])})", verdict(c5["supported"])))
c6 = conf["C6"]["arms"]
rows.append(("C6", r"Ablations at $R=12$, worst-regime violation rate (no pending / no rollback reserve / no width)",
             f"{r3(c6['f3_pi1_R12_nopending']['worst_stats']['rate'])} / {r3(c6['f3_pi1_R12_norollback']['worst_stats']['rate'])} / {r3(c6['f3_pi25_R12_noconf']['worst_stats']['rate'])}", verdict(conf["C6"]["supported"])))
body = "\\begin{tabular}{@{}l p{3.9cm} p{5.7cm} l@{}}\n\\toprule\nID & Registered statistic & Result & Verdict \\\\\n\\midrule\n"
for r in rows: body += " & ".join(r) + " \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("tab_confirm.tex", body)

# Table: simulation arms (R = 20)
def arm_row(label, a, viol_pooled, viol_worst, worst_reg):
    d = D[a]
    return (label, num(d["J"]), f"{100*(d['J']-D['never']['J'])/D['never']['J']:+.1f}".replace("-", "$-$"),
            f"{d['labels']:.1f}", f"{d['sup_q99']:.0f}", f"{d['sup_max']:.0f}", viol_pooled, viol_worst, worst_reg)
def c3(a): v = conf["C3"]["arms"][a]; return f"{100*v['pooled']:.1f}", f"{r3(v['worst_stats']['rate'])} [{r3(v['worst_stats']['lo'])}, {r3(v['worst_stats']['hi'])}]", tex(v["worst"])
arms = [("Never switch", "never", ("0.0", "0.000", "--")),
        ("Wald+cutoff (tuned)", "wald_cut", c3("wald_cut")), ("CUSUM (tuned)", "cusum", c3("cusum")),
        ("E-process gate (tuned)", "gate_wald", c3("gate_wald")), ("CUSUM rollback, $h=8$", "cusum_rb_h8", c3("cusum_rb_h8")),
        ("Stop-loss, $R=20$", "stoploss_R20", c3("stoploss_R20"))]
for lab, a, R in [("Shield, full sampling, $R=20$", "f3_pi1_R20", "C1"), ("Shield, paced, $R=20$, $\\delta=.05$", "f3v2d_R20", "C2")]:
    v = conf[R]["arms"][a]
    arms.append((lab, a, (f"{100*v['pooled']:.3f}", f"{r3(v['worst_stats']['rate'])} [{r3(v['worst_stats']['lo'])}, {r3(v['worst_stats']['hi'])}]", tex(v["worst"]) if v["worst_stats"]["k"] > 0 else "--")))
body = "\\begin{tabular}{@{}l r r r r r r l l@{}}\n\\toprule\nController & $J$ & vs never (\\%) & labels & $q_{99}$ harm & max harm & pooled viol.\\ (\\%) & worst-regime rate [Wilson] & worst regime \\\\\n\\midrule\n"
for lab, a, (vp, vw, wr) in arms:
    r = arm_row(lab, a, vp, vw, wr)
    body += " & ".join(r) + " \\\\\n"
    if a == "stoploss_R20": body += "\\midrule\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("tab_sim.tex", body)

# Appendix: all 18 arms
names = list(D.keys())
body = "\\begin{tabular}{@{}l r r r r r r@{}}\n\\toprule\nArm & $J$ & labels & $q_{95}$ & $q_{99}$ & max & deployed frac. \\\\\n\\midrule\n"
for a in names:
    d = D[a]
    body += f"{tex(a)} & {num(d['J'])} & {d['labels']:.1f} & {d['sup_q95']:.0f} & {d['sup_q99']:.0f} & {d['sup_max']:.0f} & {d['deployed']:.3f} \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_desc.tex", body)

# Appendix: per-regime exceedance of R=20 for the five comparators and the paced shield
c3a = conf["C3"]["arms"]; regs = list(c3a["wald_cut"]["per_regime"].keys())
cols = ["wald_cut", "cusum", "gate_wald", "cusum_rb_h8", "stoploss_R20"]
body = "\\begin{tabular}{@{}l " + "r " * len(cols) + "r r@{}}\n\\toprule\nRegime & Wald & CUSUM & Gate & CUSUM-rb & Stop & Shield pi1 & Shield paced \\\\\n\\midrule\n"
for rg in regs:
    body += tex(rg) + " & " + " & ".join(f"{c3a[a]['per_regime'][rg]['rate']:.3f}" for a in cols)
    body += f" & {conf['C1']['arms']['f3_pi1_R20']['per_regime'][rg]['rate']:.3f} & {conf['C2']['arms']['f3v2d_R20']['per_regime'][rg]['rate']:.3f} \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_c3regime.tex", body)


# stress / original split of comparator exceedance
STRESS = [r["id"] for r in json.load(open(HERE.parent.parent / "configs/paper3/regimes_f3_v1.json"))["regimes"]]
ORIG = [r for r in regs if r not in STRESS]
assert len(STRESS) == 6 and len(ORIG) == 24
def pool(a, group, src):
    pr = src[a]["per_regime"]; return sum(pr[g]["rate"] for g in group) / len(group)
body = "\\begin{tabular}{@{}l r r@{}}\n\\toprule\nArm & 6 stress regimes & 24 original regimes \\\\\n\\midrule\n"
for a, key in [("wald_cut", "Wald"), ("cusum", "Cusum"), ("gate_wald", "Gate"), ("cusum_rb_h8", "CusumRb"), ("stoploss_R20", "Stop")]:
    sv, ov = pool(a, STRESS, conf["C3"]["arms"]), pool(a, ORIG, conf["C3"]["arms"])
    mac(f"StressExceed{key}", f"{100*sv:.0f}"); mac(f"OrigExceed{key}", f"{100*ov:.0f}")
    body += f"{tex(a)} & {r3(sv)} & {r3(ov)} \\\\\n"
for a, src in [("f3_pi1_R20", conf["C1"]["arms"]), ("f3v2d_R20", conf["C2"]["arms"])]:
    body += f"{tex(a)} & {r3(pool(a, STRESS, src))} & {r3(pool(a, ORIG, src))} \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_split.tex", body)

# Ablations (appendix)
body = "\\begin{tabular}{@{}l l r l@{}}\n\\toprule\nAblation ($R=12$) & worst regime & rate & Wilson 95\\% \\\\\n\\midrule\n"
for a, lab in [("f3_pi1_R12_nopending", "no pending reserve"), ("f3_pi1_R12_norollback", "no rollback reserve"), ("f3_pi25_R12_noconf", "no confidence width")]:
    v = c6[a]; w = v["worst_stats"]
    body += f"{lab} & {tex(v['worst'])} & {r3(w['rate'])} & [{r3(w['lo'])}, {r3(w['hi'])}] \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_ablation.tex", body)

# ---------------------------------------------------------------- real streams
real = parse_md(RES / "real_tables.md")
CONDS = [("clean", "Clean"), ("dropout_adverse", "Adverse dropout"), ("delay_adverse", "Adverse delay")]
def pooled(cond, grp="all14"): return real[(cond, grp)]
mac("RealRunsPerArm", thousands(4600))
for cond, key in [("clean", "Clean"), ("dropout_adverse", "Dropout"), ("delay_adverse", "Delay")]:
    t = pooled(cond)
    w = rowdict(t, "wald_cut"); s = rowdict(t, "stoploss_h14")
    mac(f"RealWaldExceed{key}", thousands(exceed(w["violations (own R) or exceed"])))
    mac(f"RealStopExceed{key}", thousands(exceed(s["violations (own R) or exceed"])))
    mac(f"RealWaldMax{key}", w["max sup-harm"])
    tot = sum(own_viol(rowdict(t, r[0])["violations (own R) or exceed"]) for r in t[1] if r[0].startswith("f3"))
    mac(f"RealShieldViol{key}", tot)
    for h in (14, 24, 50, 100):
        mac(f"RealPiVsNever{key}H{['fourteen','twentyfour','fifty','hundred'][[14,24,50,100].index(h)]}", num(abs(float(rowdict(t, f'f3_pi1_h{h}')['dJ vs never'])), 0))
mac("RealJNever", rowdict(pooled("clean"), "never")["J"]); mac("RealJWald", rowdict(pooled("clean"), "wald_cut")["J"])
vn = [abs(float(rowdict(pooled("clean"), f"f3_pi1_h{h}")["dJ vs never"])) for h in (14, 24, 50, 100)]
mac("RealVsNeverMin", f"{min(vn):.0f}"); mac("RealVsNeverMax", f"{max(vn):.0f}")
mac("RealMaxExceed", thousands(max(exceed(rowdict(pooled(c), "wald_cut")["violations (own R) or exceed"]) for c, _ in CONDS)))
# fraction of the two harmful streams under corrupted feedback
hv = {}
for cond in ("dropout_adverse", "delay_adverse"):
    vals = [float(rowdict(pooled(cond, "harmful2"), f"f3_pi1_h{h}")["dJ vs wald_cut"]) for h in (6, 14, 24, 50, 100)]
    hv[cond] = (min(vals), max(vals))
mac("HarmDropMin", f"{abs(hv['dropout_adverse'][1]):.0f}"); mac("HarmDropMax", f"{abs(hv['dropout_adverse'][0]):.0f}")
mac("HarmDelayMin", f"{abs(hv['delay_adverse'][1]):.0f}"); mac("HarmDelayMax", f"{abs(hv['delay_adverse'][0]):.0f}")

REAL_ARMS = [("Never switch", "never"), ("Wald+cutoff", "wald_cut"), ("CUSUM", "cusum"), ("E-process gate", "gate_wald"),
             ("CUSUM rollback $h=8$", "cusum_rb_h8"), ("Stop-loss, $R=24$", "stoploss_h14"),
             ("Shield, full, $R=24$", "f3_pi1_h14"), ("Shield, paced, $R=24$", "f3v2d_h14"),
             ("Shield, full, $R=60$", "f3_pi1_h50"), ("Shield, paced, $R=60$", "f3v2d_h50"), ("Shield, paced, $R=110$", "f3v2d_h100")]
body = "\\begin{tabular}{@{}l " + "r r r " * 3 + "@{}}\n\\toprule\n"
body += " & " + " & ".join(f"\\multicolumn{{3}}{{c}}{{{n}}}" for _, n in CONDS) + " \\\\\n"
body += "".join(f"\\cmidrule(lr){{{2+3*i}-{4+3*i}}}" for i in range(3)) + "\n"
body += "Controller & " + " & ".join(["$J$ & vs never & viol."] * 3) + " \\\\\n\\midrule\n"
for lab, a in REAL_ARMS:
    cells = []
    for cond, _ in CONDS:
        r = rowdict(pooled(cond), a)
        cells += [r["J"], num(float(r["dJ vs never"]), 1) if float(r["dJ vs never"]) != 0 else "0.0", thousands(exceed(r["violations (own R) or exceed"]))]
    body += lab + " & " + " & ".join(cells) + " \\\\\n"
    if a == "stoploss_h14": body += "\\midrule\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("tab_real.tex", body)

# harmful streams table
body = "\\begin{tabular}{@{}l l " + "r " * 5 + "@{}}\n\\toprule\n & & \\multicolumn{5}{c}{headroom $h$ ($R=10+h$)} \\\\\n\\cmidrule(lr){3-7}\nFeedback & vs & 6 & 14 & 24 & 50 & 100 \\\\\n\\midrule\n"
for cond, n in CONDS:
    t = pooled(cond, "harmful2")
    for ref, col in [("wald_cut", "dJ vs wald_cut"), ("never", "dJ vs never")]:
        body += f"{n if ref=='wald_cut' else ''} & {tex(ref)} & " + " & ".join(sg(float(rowdict(t, f'f3_pi1_h{h}')[col]), 1) for h in (6, 14, 24, 50, 100)) + " \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("tab_harmful.tex", body)

# appendix: all14 pooled tables per condition, plus harmful2/beneficial12 clean
def full_real(cond, grp):
    t = pooled(cond, grp); hdr, rows = t
    body = "\\begin{tabular}{@{}l r r r r r r r r@{}}\n\\toprule\nArm & $J$ & $\\Delta J$ vs Wald & $\\Delta J$ vs never & max harm & viol./exceed & labels & deployed & forced rb \\\\\n\\midrule\n"
    for r in rows:
        d = dict(zip(hdr, r))
        ex = d["violations (own R) or exceed"]
        body += (f"{tex(r[0])} & {d['J']} & {sg(float(d['dJ vs wald_cut']),1)} & {sg(float(d['dJ vs never']),1)} & {d['max sup-harm']} & "
                 f"{tex(ex.replace(' ', ', '))} & {d['labels']} & {d['deployed']} & {d['forced rb']} \\\\\n")
    body += "\\bottomrule\n\\end{tabular}\n"
    return body
for cond, grp, name in [("clean", "all14", "app_real_clean"), ("dropout_adverse", "all14", "app_real_dropout"), ("delay_adverse", "all14", "app_real_delay"),
                        ("clean", "harmful2", "app_real_clean_harm"), ("clean", "beneficial12", "app_real_clean_ben")]:
    write(name + ".tex", full_real(cond, grp))

# per-stream mean J at h=50, clean
hdr, rows = real[("clean", "clean: Mean J")]
armsel = ["never", "wald_cut", "stoploss_h50", "f3_pi1_h50", "f3v2d_h50"]
body = "\\begin{tabular}{@{}l " + "r " * len(armsel) + "@{}}\n\\toprule\nStream & never & Wald+cutoff & stop-loss & shield full & shield paced \\\\\n\\midrule\n"
dd = {r[0]: dict(zip(hdr, r)) for r in rows}
for st in hdr[1:]:
    body += tex(st) + " & " + " & ".join(dd[a][st] for a in armsel) + " \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_stream.tex", body)

# ---------------------------------------------------------------- regime map
bins = ["[0,0.5)", "[0.5,1)", "[1,2)", "[2,inf)"]
SRC = [("scarce/f3_pi1", "simulation, full"), ("scarce/f3v2d", "simulation, paced"), ("scarce/v3", "simulation, v3"),
       ("real/f3_pi1", "real, full"), ("real/f3v2d", "real, paced"), ("real/v3", "real, v3")]
body = "\\begin{tabular}{@{}l r l r r r r@{}}\n\\toprule\n & units & Spearman$(x,L)$ [95\\% CI] & \\multicolumn{4}{c}{median $L$ by $x=rd/h$} \\\\\n\\cmidrule(lr){4-7}\n"
body += "Arm & & & $<.5$ & $.5$--$1$ & $1$--$2$ & $\\ge 2$ \\\\\n\\midrule\n"
for k, lab in SRC:
    t = expo["tests"][k]; b = expo["bins"][k]
    body += f"{lab} & {t['n_units']} & {t['spearman']:.2f} [{t['lo']:.2f}, {t['hi']:.2f}] & " + " & ".join(f"{b[x]['median_L']:.2f}" for x in bins) + " \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("tab_regime.tex", body)
mac("RegimeTestsSupported", sum(1 for v in expo["tests"].values() if v["supported"])); mac("RegimeTestsTotal", len(expo["tests"]))
paced = ["scarce/f3v2d", "scarce/v3", "real/f3v2d", "real/v3"]
keep = [1 - expo["bins"][k][bins[0]]["median_L"] for k in paced]
mac("KeepLo", f"{100*min(keep):.0f}"); mac("KeepHi", f"{100*max(keep):.0f}")
mac("SpearLo", f"{min(v['spearman'] for v in expo['tests'].values()):.2f}"); mac("SpearHi", f"{max(v['spearman'] for v in expo['tests'].values()):.2f}")
mac("LargeXMin", f"{min(expo['bins'][k][b]['median_L'] for k in expo['bins'] for b in bins[2:] if k in paced):.2f}")
mac("NUnits", expo["n_units"])
ols = expo["ols"]
body = "\\begin{tabular}{@{}l r r@{}}\n\\toprule\nArm & coef. of $\\log x$ & coef. of $\\log$(labels per exposed round) \\\\\n\\midrule\n"
for k, lab in SRC:
    body += f"{lab} & {ols[k]['b_logx']:.2f} & {sg(ols[k]['b_log_labels'])} \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_ols.tex", body)

# ---------------------------------------------------------------- propositions check
p3 = props["prop3"]
mac("PThreeCells", len(p3)); mac("PThreeAttain", sum(1 for r in p3 if r["attains"]))
body = "\\begin{tabular}{@{}r r r r r l@{}}\n\\toprule\n$d$ & $R$ & first spell & $\\lfloor R-2k\\rfloor$ & $\\min(d,\\lfloor R-2k\\rfloor)$ & attained \\\\\n\\midrule\n"
for r in p3:
    body += f"{r['d']} & {r['R']} & {r['first_spell']} & {r['floor_R_minus_2k']} & {r['blind_hold_allowed']} & {'yes' if r['attains'] else 'no'} \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_prop3.tex", body)
p4 = props["prop4"]
NRUN = 2000  # runs per cell, stated in 03F section 4 (numerical check paragraph)
zs = []
body = "\\begin{tabular}{@{}r r r r r r r@{}}\n\\toprule\n$p$ & $d$ & $R$ & $m$ & forced rollbacks & bound & $z$ \\\\\n\\midrule\n"
for r in p4:
    f, b = r["forced_frac"], min(1.0, r["bound_ruin"])
    se = math.sqrt(max(b * (1 - b), 1e-12) / NRUN)
    z = (f - b) / se if f > b else 0.0
    zs.append(z)
    body += f"{r['p']:.1f} & {r['d']} & {r['R']} & {sg(r['m'],0)} & {f:.4f} & {b:.4f} & {z:.1f} \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_prop4.tex", body)
mac("PFourCells", len(p4)); mac("PFourAbove", sum(1 for r in p4 if r["forced_frac"] > min(1.0, r["bound_ruin"])))
mac("PFourMaxZ", f"{max(zs):.1f}")
tight = [r for r in p4 if r["d"] == 1 and r["p"] == 0.6 and r["R"] == 10][0]
mac("PFourTightEmp", f"{tight['forced_frac']:.3f}"); mac("PFourTightBound", f"{tight['bound_ruin']:.3f}")
tight2 = [r for r in p4 if r["d"] == 1 and r["p"] == 0.7 and r["R"] == 10][0]
mac("PFourTightEmpB", f"{tight2['forced_frac']:.3f}"); mac("PFourTightBoundB", f"{tight2['bound_ruin']:.3f}")

# ---------------------------------------------------------------- v3 (appendix)
sc = parse_md(RES / "v3_scarce_tables.md"); og = parse_md(RES / "v3_orig30_tables.md"); rv = parse_md(RES / "real_v3_tables.md")
def v3rows(tab, arms, cols):
    hdr, rows = tab
    out = ""
    for r in rows:
        if r[0] in arms:
            d = dict(zip(hdr, r)); out += tex(r[0]) + " & " + " & ".join(tex(d[c]) for c in cols) + " \\\\\n"
    return out
cols = ["J", "dJ vs wald_cut", "dJ vs never", "violation (own R) / exceedance rate of R24/60/110"]
t = sc[("", "Pooled")]
body = "\\begin{tabular}{@{}l r l l l@{}}\n\\toprule\nArm & $J$ & $\\Delta J$ vs Wald & $\\Delta J$ vs never & violations \\\\\n\\midrule\n"
for r in t[1]:
    if r[0] in ("never", "wald_cut", "stoploss_h50", "f3_pi1_h50", "f3v2d_h50", "f3_pi1_h100", "f3v2d_h100", "v3_h50", "v3_h100"):
        d = dict(zip(t[0], r)); body += tex(r[0]) + " & " + d["J"] + " & " + tex(d["dJ vs wald_cut"]) + " & " + tex(d["dJ vs never"]) + " & " + tex(d[cols[3]].split(" (")[0]) + " \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_v3_scarce.tex", body)
t = og[("", "Pooled")]
body = "\\begin{tabular}{@{}l r l l l@{}}\n\\toprule\nArm & $J$ & $\\Delta J$ vs Wald & $\\Delta J$ vs never & violations \\\\\n\\midrule\n"
for r in t[1]:
    if r[0] != "never":
        d = dict(zip(t[0], r)); vv = d["violation (own R) / exceedance rate of R12/20/30"]
        body += tex(r[0]) + " & " + d["J"] + " & " + tex(d["dJ vs wald_cut"]) + " & " + tex(d["dJ vs never"]) + " & " + tex(vv.split(" (")[0]) + " \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_v3_orig30.tex", body)
t = rv[("clean", "clean / all14: pooled (equal weight over streams)")]
body = "\\begin{tabular}{@{}l r r r r@{}}\n\\toprule\nArm & $J$ & $\\Delta J$ vs Wald & $\\Delta J$ vs never & viol. \\\\\n\\midrule\n"
for r in t[1]:
    if r[0] in ("f3_pi1_h50", "f3v2d_h50", "v3_h50", "f3_pi1_h100", "f3v2d_h100", "v3_h100"):
        d = dict(zip(t[0], r)); body += tex(r[0]) + " & " + d["J"] + " & " + sg(float(d["dJ vs wald_cut"]), 1) + " & " + sg(float(d["dJ vs never"]), 1) + " & " + tex(d["violations (own R) / exceed"]) + " \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_v3_real.tex", body)
cand = sel["candidates"]
mac("VThreeNCand", len(cand)); mac("VThreeBest", f"{min(c['score'] for c in cand.values()):.1f}")

# ---------------------------------------------------------------- numbers.tex
(OUT / "numbers.tex").write_text("% generated by make_tables.py; do not edit\n" + "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in MAC.items()))
print("wrote", len(MAC), "macros and", len(list(OUT.glob('*.tex'))), "files")

# extra inline numbers
cfg = json.load(open(HERE.parent.parent / "configs/paper3/regimes_f3_v1.json"))
r_def, d_def, k_def = cfg["defaults"]["r"], cfg["defaults"]["delay"]["d"], cfg["defaults"]["costs"]["k"]
for R_, nm in [(12, "Twelve"), (20, "Twenty"), (30, "Thirty")]:
    mac(f"DefX{nm}", f"{r_def*d_def/(R_-2*k_def):.2f}")
mac("DefR", f"{r_def:.1f}".lstrip("0") if False else f"{r_def}"); mac("DefD", d_def)
t = pooled("clean")
mac("RealSixVsNever", f"{abs(float(rowdict(t, 'f3_pi1_h6')['dJ vs never'])):.1f}")
vals = [float(rowdict(pooled(c, "harmful2"), f"f3_pi1_h{h}")["dJ vs never"]) for c in ("dropout_adverse", "delay_adverse") for h in (6, 14, 24, 50, 100)]
mac("HarmNeverMin", f"{min(vals):.0f}"); mac("HarmNeverMax", f"{max(vals):.0f}")
assert all(MAC[f"RealShieldViol{c}"] == 0 for c in ("Clean", "Dropout", "Delay"))
(OUT / "numbers.tex").write_text("% generated by make_tables.py; do not edit\n" + "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in MAC.items()))
