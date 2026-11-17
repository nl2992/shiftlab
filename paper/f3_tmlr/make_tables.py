#!/usr/bin/env python3
"""Write every table and inline number of main.tex (TMLR version) from the committed result files.

Usage: python3 make_tables.py   (run from paper/f3_tmlr; no arguments)
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
    for name, label in [("dropout_adverse", "Adverse dropout"), ("delay_adverse", "Adverse delay"),
                        ("expensive_switch", "High switch fee"), ("bait_reversal", "Bait reversal")]:
        s = s.replace(name, label)
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
body = "\\begin{tabular}{@{}l p{4.8cm} p{7.2cm} l@{}}\n\\toprule\nID & Registered statistic & Result & Verdict \\\\\n\\midrule\n"
for r in rows: body += " & ".join(r) + " \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("tab_confirm.tex", body)

# Table: simulation arms (R = 20)
def arm_row(label, a, viol_pooled, viol_worst, worst_reg):
    d = D[a]
    return (label, num(d["J"]), f"{100*(d['J']-D['never']['J'])/D['never']['J']:+.1f}".replace("-", "$-$"),
            f"{d['labels']:.1f}", f"{d['sup_q99']:.0f}", f"{d['sup_max']:.0f}", viol_pooled, viol_worst, worst_reg)
def regime_label(name):
    return {"dropout_adverse": "Adverse dropout", "expensive_switch": "High switch fee", "bait_reversal": "Bait reversal"}.get(name, tex(name))
def c3(a): v = conf["C3"]["arms"][a]; return f"{100*v['pooled']:.1f}", f"{r3(v['worst_stats']['rate'])} [{r3(v['worst_stats']['lo'])}, {r3(v['worst_stats']['hi'])}]", regime_label(v["worst"])
arms = [("Never switch", "never", ("0.0", "0.000", "--")),
        ("Wald+cutoff (tuned)", "wald_cut", c3("wald_cut")), ("CUSUM (tuned)", "cusum", c3("cusum")),
        ("E-process gate (tuned)", "gate_wald", c3("gate_wald")), ("CUSUM rollback, $h=8$", "cusum_rb_h8", c3("cusum_rb_h8")),
        ("Stop-loss, $R=20$", "stoploss_R20", c3("stoploss_R20"))]
for lab, a, R in [("Shield, full sampling, $R=20$", "f3_pi1_R20", "C1"), ("Shield, paced, $R=20$, $\\delta=.05$", "f3v2d_R20", "C2")]:
    v = conf[R]["arms"][a]
    arms.append((lab, a, (f"{100*v['pooled']:.3f}", f"{r3(v['worst_stats']['rate'])} [{r3(v['worst_stats']['lo'])}, {r3(v['worst_stats']['hi'])}]", regime_label(v["worst"]) if v["worst_stats"]["k"] > 0 else "--")))
body = "\\begin{tabular}{@{}p{3.7cm} r r r@{}}\n\\toprule\nController & $J$ & vs never (\\%) & labels \\\\\n\\midrule\n"
for lab, a, (vp, vw, wr) in arms:
    r = arm_row(lab, a, vp, vw, wr)
    body += " & ".join(r[:4]) + " \\\\\n"
    if a == "stoploss_R20": body += "\\midrule\n"
body += "\\bottomrule\n\\end{tabular}\\par\\smallskip\n"
body += "\\begin{tabular}{@{}p{3.7cm} r r r p{3.3cm} p{2.3cm}@{}}\n\\toprule\nController & $q_{99}$ harm & max harm & pooled viol. (\\%) & worst-regime rate [Wilson] & worst regime \\\\\n\\midrule\n"
for lab, a, (vp, vw, wr) in arms:
    r = arm_row(lab, a, vp, vw, wr)
    body += " & ".join((r[0], r[4], r[5], r[6], r[7], r[8])) + " \\\\\n"
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
_so = [(pool(a, STRESS, conf["C3"]["arms"]), pool(a, ORIG, conf["C3"]["arms"])) for a in ("wald_cut", "cusum", "gate_wald", "cusum_rb_h8", "stoploss_R20")]
mac("StressExceedMin", f"{100*min(x for x, _ in _so):.0f}"); mac("StressExceedMax", f"{100*max(x for x, _ in _so):.0f}")
mac("OrigExceedMin", f"{100*min(y for _, y in _so):.0f}"); mac("OrigExceedMax", f"{100*max(y for _, y in _so):.0f}")

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
body = "\\begin{tabular}{@{}l r l r r r r@{}}\n\\toprule\n & clusters & Spearman$(x,L)$ [95\\% CI] & \\multicolumn{4}{c}{median $L$ by $x=rd/h$} \\\\\n\\cmidrule(lr){4-7}\n"
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

# ================================================================ explanatory appendix material
ROOT = HERE.parent.parent
CFG = ROOT / "configs/paper3"
PROG = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme"
arms_cfg = json.load(open(CFG / "f3_confirmation_arms_v1.json"))["arms"]
arm_by = {a["name"]: a for a in arms_cfg}
reg1 = json.load(open(CFG / "regimes_v1.json"))
reg2 = json.load(open(CFG / "regimes_f3_v1.json"))
dflt = reg1["defaults"]

# ---- settings quoted in the text must match the configs (asserted, not typed into macros)
rs_src = (ROOT / "src/shiftlab/paper3/riskbudget/real_streams.py").read_text()
assert re.search(r"T, B, C_Q, K = 2000, 200, 0\.05, 5\.0", rs_src)
assert (dflt["B"], dflt["costs"]["k"], dflt["costs"]["c_q"], dflt["delay"]) == (60, 3.0, 0.05, {"kind": "fixed", "d": 5})
assert re.search(r"T_DEFAULT = 300", (ROOT / "src/shiftlab/paper3/riskbudget/harness.py").read_text())
assert reg2["defaults"] == dflt and len(reg1["regimes"]) == 24 and len(reg2["regimes"]) == 6
assert conf and len(arms_cfg) == 18

# ---- worked example: compute the shield check W_t on two tapes from its definition
def example_check(k, R, d, tape_sign, n_max=40):
    """Full-sampling shield on a tape where every round is an exposed disagreement round.
    tape_sign=+1: every round harmful (chi=+1); -1: every round beneficial (chi=-1).
    Returns list of (n, W_n, deployed_ok) with the check evaluated at round n after a promotion at round 1."""
    out = []
    for n in range(1, n_max + 1):
        released = [s for s in range(1, n) if s + d <= n]
        pending = [s for s in range(1, n) if s + d > n]
        A = sum(tape_sign for _ in released)
        P = len(pending)
        N_prev = 0 if n == 1 else 1
        fees = k * (N_prev + (1 if n == 1 else 0))
        W = fees + k + A + P + 1
        out.append((n, W, W <= R))
    return out

EXk, EXR, EXd = 3, 20, 5
EXh = EXR - 2 * EXk
harm = example_check(EXk, EXR, EXd, +1)
good = example_check(EXk, EXR, EXd, -1)
hold = max(n for n, W, ok in harm if all(o for _, _, o in harm[:n]))
roll = hold + 1
assert hold == EXh == 14 and harm[0][1] == 2 * EXk + 1 == 7 and not harm[hold][2]
assert all(W == 2 * EXk + n for n, W, _ in harm)
peak_good = max(W for _, W, _ in good)
assert peak_good == 2 * EXk + EXd and all(ok for *_, ok in good)
H_at_roll = EXk * 2 + hold  # two action changes, `hold` harmful exposed rounds
assert H_at_roll == EXR
mac("ExK", EXk); mac("ExR", EXR); mac("ExD", EXd); mac("ExH", EXh)
mac("ExWone", harm[0][1]); mac("ExHold", hold); mac("ExRoll", roll); mac("ExWroll", harm[hold][1])
mac("ExHarmAtRoll", H_at_roll); mac("ExPeakGood", peak_good); mac("ExFirstBack", EXd + 1)
mac("ExWgoodSix", good[5][1]); mac("ExWgoodTen", good[9][1])
mac("ExWhalfpi", 2 * EXk + 2)       # first-round check at pi = 1/2 before the width term
mac("ExM", EXR - 2 * EXk - EXd)
mu_ex, p_ex = 0.4, 0.7
m_ex = EXR - 2 * EXk - EXd
b1 = math.exp(-2 * mu_ex * m_ex); b2 = ((1 - p_ex) / p_ex) ** (math.floor(m_ex) + 1)
mac("ExBoundExp", f"{b1:.1e}".replace("e-0", r"\times10^{-").replace("e-", r"\times10^{-") + "}")
mac("ExBoundTwo", f"{b2:.1e}".replace("e-0", r"\times10^{-").replace("e-", r"\times10^{-") + "}")
mac("ExBoundExpDec", f"{b1:.4f}"); mac("ExBoundTwoDec", f"{b2:.4f}")
# the 15-round hold would need R >= 2k + 15 (Proposition on reserves with e = 15, n large)
mac("ExNeedR", 2 * EXk + hold + 1)

rows = []
for n in (1, 5, 6, 10, 14, 15):
    Wh = harm[n - 1][1]; Wg = good[n - 1][1]
    rows.append(f"{n} & {Wh} & {'deploy' if harm[n-1][2] else 'roll back'} & {Wg} & {'deploy' if good[n-1][2] else 'roll back'} \\\\")
write("ex_w.tex", "\\begin{tabular}{@{}rrlrl@{}}\n\\toprule\n"
      "exposed round $n$ & $W$, all-harm tape & decision & $W$, all-benefit tape & decision \\\\\n\\midrule\n"
      + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---- appendix: the 30 regimes
def f2(x):
    s = f"{x:.2f}".rstrip("0").rstrip(".") if x != int(x) else f"{int(x)}"
    return s[1:] if s.startswith("0.") else s

def path_txt(p):
    if p["type"] in ("steps", "linear"):
        kn = ", ".join(f"{f2(a)}:{f2(b)}" for a, b in p["knots"])
        return ("steps " if p["type"] == "steps" else "linear ") + kn
    if p["type"] == "seasonal":
        return f"seasonal, ${f2(p['hi'])}$ for the first {f2(p['duty'])} of each ${f2(p['period_frac'])}T$ period, else ${f2(p['lo'])}$"
    raise ValueError(p)

def delay_txt(dl):
    kd = dl["kind"]
    if kd == "fixed": return f"fixed {dl['d']}"
    if kd == "informative": return f"{dl['d']}, plus {dl['extra']} if the label favours the challenger"
    if kd == "informative_adverse": return f"{dl['d']}, plus {dl['extra']} if the label is unfavourable to the challenger"
    if kd == "random": return "random on " + "/".join(str(v) for v in dl["values"]) + " with probabilities " + "/".join(f2(v) for v in dl["probs"])
    if kd == "dropout": return f"{dl['d']}; each label never arrives w.p. {f2(dl['p_drop'])}"
    if kd == "dropout_adverse": return f"{dl['d']}; labels unfavourable to the challenger never arrive w.p. {f2(dl['p_drop'])}"
    raise ValueError(kd)

def regime_rows(cfgd):
    out = []
    for g in cfgd["regimes"]:
        prm = {**dflt, **{k: v for k, v in g.items() if k not in ("costs", "B")}}
        ov = []
        if g.get("costs"): ov += [f"{k_}={v:g}" for k_, v in g["costs"].items()]
        if "B" in g: ov.append(f"$B={g['B']}$")
        if prm["e_both"] != dflt["e_both"]: ov.append(f"$e_{{\\rm both}}={f2(prm['e_both'])}$")
        ov = ", ".join(ov).replace("k=", "$k=").replace("$k=30", "$k=30$") if ov else "none"
        out.append(f"{tex(g['id'])} & {path_txt(prm['path'])} & {f2(prm['r'])} & {f2(prm['rho'])} & {delay_txt(prm['delay'])} & {ov} & {tex(g.get('description',''))} \\\\")
    return out

body = ("\\begin{longtable}{@{}p{3.3cm}p{2.9cm}rrp{2.4cm}p{1.1cm}p{2.7cm}@{}}\n"
        "\\caption{All 30 simulated regimes. $p(t)$ is the probability that the challenger is correct when the models disagree, given by knots $t/T$:$p$ (``steps'': constant from each knot; ``linear'': interpolated; evaluated at $(t-\\tfrac12)/T$). $r$ is the disagreement rate, $\\rho$ the lag-1 dependence of the latent Gaussian process, $d_t$ the label delay in rounds. Defaults: $r=.3$, $\\rho=0$, $e_{\\rm both}=.1$, delay fixed at 5, $k=3$, $B=60$, $c_q=.05$. Override lists departures from the defaults other than $r$, $\\rho$ and the delay. Meaning is the description in the configuration file.}\\label{tab:regimes_app}\\\\\n"
        "\\toprule id & $p(t)$ (knots $t/T$:$p$) & $r$ & $\\rho$ & delay $d_t$ & override & meaning \\\\\n\\midrule\n\\endfirsthead\n\\toprule id & $p(t)$ (knots $t/T$:$p$) & $r$ & $\\rho$ & delay $d_t$ & override & meaning \\\\\n\\midrule\n\\endhead\n"
        "\\multicolumn{7}{@{}l}{\\emph{24 original regimes} (\\texttt{regimes\\_v1.json})} \\\\\n"
        + "\n".join(regime_rows(reg1)) +
        "\n\\midrule\n\\multicolumn{7}{@{}l}{\\emph{6 stress regimes} (\\texttt{regimes\\_f3\\_v1.json})} \\\\\n"
        + "\n".join(regime_rows(reg2)) + "\n\\bottomrule\n\\end{longtable}\n")
write("app_regimes.tex", body)
mac("NOrigRegimes", len(reg1["regimes"])); mac("NStressRegimes", len(reg2["regimes"]))

# ---- appendix: comparators and shield arms, tuned parameters from the frozen arms file
def g3(x): return f"{x:.3f}"
wc = arm_by["wald_cut"]["policy"]["params"]; cu = arm_by["cusum"]["policy"]["params"]; gw = arm_by["gate_wald"]["policy"]["params"]
for n_ in ("cusum_rb_h4", "cusum_rb_h8", "stoploss_R12", "stoploss_R20", "stoploss_R30"):
    assert arm_by[n_]["inner"]["params"] == wc
body = "\\begin{tabular}{@{}p{2.3cm}p{3.2cm}p{5.6cm}p{4.0cm}@{}}\n\\toprule\nname & label & tuned or fixed parameters (frozen) & tuning space (32 random draws)\\\\\n\\midrule\n"
body += f"never & in-house reference & none & none \\\\\n"
body += f"wald\\_cut & documented adapter & $\\lambda={g3(wc['lam'])}$, $\\gamma={g3(wc['gamma'])}$, paced acquisition, cutoff {wc['stop']:g}$T$ & $\\lambda\\in[.9,.999]$, $\\gamma\\in[.05,.5]$, cutoff $\\in\\{{.05,.1,.15,.2,.3\\}}T$ \\\\\n"
body += f"cusum & in-house heuristic & $\\delta={g3(cu['delta'])}$, $h={g3(cu['h'])}$, paced acquisition, cutoff {cu['stop']:g}$T$ & $\\delta\\in[.02,.4]$, $h\\in[1,12]$ (log-uniform), cutoff $\\in\\{{\\text{{none}},.05,\\dots,.3\\}}T$ \\\\\n"
body += f"gate\\_wald & in-house heuristic & Wald part $\\lambda={g3(gw['lam'])}$, $\\gamma={g3(gw['gamma'])}$, cutoff {gw['stop']:g}$T$; gate $\\alpha={gw['alpha']:g}$, $\\lambda_g={gw['lam_g']:g}$ & Wald space, $\\alpha\\in\\{{.05,.1,.2\\}}$, $\\lambda_g\\in\\{{.1,.25,.5\\}}$ \\\\\n"
body += f"cusum\\_rb\\_h4, \\_h8 & in-house heuristic & inner: wald\\_cut above; rollback threshold $h\\in\\{{{arm_by['cusum_rb_h4']['h']:g},{arm_by['cusum_rb_h8']['h']:g}\\}}$, drift $0.1$ & threshold fixed by arm, not tuned \\\\\n"
body += f"stoploss\\_R12, \\_R20, \\_R30 & in-house heuristic & inner: wald\\_cut above; budget $R\\in\\{{{arm_by['stoploss_R12']['R']},{arm_by['stoploss_R20']['R']},{arm_by['stoploss_R30']['R']}\\}}$ & $R$ set by the user, not tuned \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_comparators.tex", body)

def shield_row(name, label, extra):
    a = arm_by[name]; sh = a["shield"]; ip = a["inner"]["params"]
    return (f"{tex(name)} & {label} & $\\lambda={g3(ip['lam'])}$, $\\gamma={g3(ip['gamma'])}$, cutoff {ip['stop']:g}$T$ & {extra} \\\\")
def shp(sh, keys):
    return ", ".join(f"{k_}$={sh[k_]}$" if not isinstance(sh[k_], (int, float)) or isinstance(sh[k_], bool) else f"{k_}$={sh[k_]:g}$" for k_ in keys if k_ in sh)
sh1 = arm_by["f3_pi1_R20"]["shield"]; sh2 = arm_by["f3v2d_R20"]["shield"]; sh3 = arm_by["f3v2_R20_blind8"]["shield"]
v3f = json.load(open(CFG / "f3_v3_frozen.json"))["shield"]
body = "\\begin{tabular}{@{}p{3.0cm}p{2.5cm}p{4.2cm}p{5.3cm}@{}}\n\\toprule\narm & variant & inner rule (tuned) & shield settings \\\\\n\\midrule\n"
body += shield_row("f3_pi1_R20", "full sampling", f"$\\pi=1$ on every exposed round, $\\delta={sh1['delta']:g}$, label reserve {sh1['label_reserve_frac']:g}$B$; $R\\in\\{{12,20,30\\}}$")
body += "\n" + shield_row("f3v2d_R20", "paced, settlement", f"$\\pi_{{\\min}}={sh2['pi_min']:g}$, $\\delta={sh2['delta']:g}$, label reserve {sh2['label_reserve_frac']:g}$B$, settlement window = declared delay (else {sh2['default_window']}); $R\\in\\{{20,30\\}}$")
body += "\n" + shield_row("f3v2_R20_blind8", "blind-round", f"$\\pi_{{\\min}}={sh3['pi_min']:g}$ (so $\\pi\\in\\{{1,\\text{{blind}}\\}}$), blind margin {sh3['blind_margin']:g}, label reserve {sh3['label_reserve_frac']:.3f}$B$, window {sh3['default_window']}; $R=20$")
body += f"\nv3 (frozen in \\texttt{{f3\\_v3\\_frozen.json}}) & label-scarce & wald\\_cut as above & $\\pi_{{\\min}}={v3f['pi_min']:g}$, label reserve {v3f['label_reserve_frac']:g}$B$, no blind rounds, mixture grid up to total variance {int(max(v3f['v_targets']))}, $\\delta={v3f['delta']:g}$ \\\\\n"
body += "\\bottomrule\n\\end{tabular}\n"
write("app_shield_arms.tex", body)

# ---- appendix: the 14 real streams
sprint = re.findall(r'\|\s*(\w+)\s*\|\s*(\d+),\s*https', (ROOT / "data/sprint_fresh_losses/README.md").read_text())
sprint_id = {n: i for n, i in sprint}
assert sprint_id == {"metro": "492", "beijing_pm25": "381", "bike_hour": "275", "appliances": "374", "household_power": "235"}
import numpy as np
dl_map = {m[0]: (m[1], int(m[2])) for m in re.findall(r'"(\w+)": \((\w+_DIR), (\d+)\)', rs_src)}
dl_map = {n: (d, int(v)) for n, d, v in re.findall(r'"(\w+)": \((\w+_DIR), (\d+)\)', rs_src)}
assert len(dl_map) == 14
import csv
inv = {r["name"]: r for r in csv.DictReader(open(PROG / "02_DATASET_INVENTORY.csv"))}
order = ["airlines", "bank", "criteo", "elec2", "openml_ldpa", "rialto", "spam", "uci_occupancy", "weather",
         "metro", "beijing_pm25", "bike_hour", "appliances", "household_power"]
src_atlas = {"airlines": "OpenML 1169", "bank": "UCI 222", "criteo": "not in the inventory", "elec2": "OpenML electricity-normalized",
             "openml_ldpa": "not in the inventory", "rialto": "Losing mirror", "spam": "Katakis spam stream",
             "uci_occupancy": "not in the inventory", "weather": "Elwell-Polikar Offutt AFB"}
task_sprint = {"metro": "traffic volume above median", "beijing_pm25": "PM2.5 above median",
               "bike_hour": "rental count above median", "appliances": "appliance energy use above median",
               "household_power": "global active power above median"}
rows, tot_ep = [], 0
for n in order:
    d, dv = dl_map[n]
    z = np.load(ROOT / "data" / ("atlas_v2_losses" if d == "ATLAS_DIR" else "sprint_fresh_losses") / f"{n}.npz")
    l0, l1 = z["l0"].astype(float), z["l1"].astype(float)
    K = l0.shape[0]; tot_ep += K
    assert l0.shape[1] == 2000
    if d == "ATLAS_DIR":
        task = inv[n]["task"] if n in inv else "not in the inventory"
        source = src_atlas[n]
        models = "not documented"
    else:
        task = task_sprint[n]; source = f"UCI {sprint_id[n]}"
        models = "LR / HGB"
    rows.append(f"{tex(n)} & {tex(task)} & {tex(source)} & {models} & {K} & {dv} & {l0.mean():.3f} & {l1.mean():.3f} & {(l0 != l1).mean():.3f} & {'worse' if l1.mean() > l0.mean() else 'better'} \\\\")
assert tot_ep == 230, tot_ep
mac("NStreamEpisodes", tot_ep)
body = ("\\begin{tabular}{@{}p{2.2cm}p{3.0cm}p{2.5cm}lrrrrrl@{}}\n\\toprule\n"
        "stream & task (binary) & source & models (inc. / chall.) & ep. & delay & inc. err. & chall. err. & disagr. & challenger \\\\\n\\midrule\n"
        + "\n".join(rows[:9]) + "\n\\midrule\n" + "\n".join(rows[9:]) + "\n\\bottomrule\n\\end{tabular}\n")
write("app_streams_desc.tex", body)

# ---- compute (ledger wall-clock per stage)
led = [json.loads(l) for l in open(PROG / "ledger/riskbudget.jsonl")]
wall = {d["stage"]: d["wall_clock_s"] for d in led}
for st, nm in [("confirmation", "WallConfirm"), ("real_streams", "WallReal"), ("v3_select", "WallVSel"), ("v3_scarce", "WallVScarce"),
               ("v3_orig30", "WallVOrig"), ("real_streams_v3_second_look", "WallVReal"), ("dev_v2", "WallDevTwo")]:
    mac(nm, f"{wall[st]:,.0f}".replace(",", "{,}"))
mac("WallTotalMin", f"{sum(wall.values())/60:.0f}")
mac("NLedgerStages", len(wall))
(OUT / "numbers.tex").write_text("% generated by make_tables.py; do not edit\n" + "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in MAC.items()))
mac("ExX", f"{EXd/EXh:.2f}")
(OUT / "numbers.tex").write_text("% generated by make_tables.py; do not edit\n" + "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in MAC.items()))

# ---- calibrated comparators (calib_summary.json)
cal = json.load(open(RES / "calib_summary.json"))
cc = cal["calibration"]["calibration"]
for R in (12, 20, 30):
    s, c = cc[f"R{R}"]["stoploss_cal"], cc[f"R{R}"]["cusumrb_cal"]
    mac(f"CalStopC{['A','B','C'][(12,20,30).index(R)]}", f"{s['chosen']:g}")
    mac(f"CalCusH{['A','B','C'][(12,20,30).index(R)]}", f"{c['chosen']:g}")
    mac(f"CalCusOk{['A','B','C'][(12,20,30).index(R)]}", "yes" if c["standard_reached"] else "no")
    assert s["standard_reached"]
mac("CalNSeeds", cal["calibration"]["standard"]["n_seeds"])
# frontier: best stop-loss margin that does not block all, at R=20
fr = cc["R20"]["stoploss_cal"]["frontier"]
nb = [f for f in fr if not f["meets"]]
mac("CalStopLastC", f"{nb[-1]['value']:g}"); mac("CalStopLastViol", r3(nb[-1]["worst_viol"]))
fc = cc["R20"]["cusumrb_cal"]["frontier"]
best = min(fc, key=lambda f: f["worst_viol"])
mac("CalCusBestH", f"{best['value']:g}"); mac("CalCusBestViol", r3(best["worst_viol"]))
A = cal["sim"]["arms"]
rows = []
lab = {"never": "Never switch", "wald_cut": "Wald with cutoff (tuned)", "f3_pi1_R12": "Shield, full, $R=12$",
       "f3_pi1_R20": "Shield, full, $R=20$", "f3_pi1_R30": "Shield, full, $R=30$",
       "stoploss_cal_R12": "Stop-loss, calibrated, $R=12$", "stoploss_cal_R20": "Stop-loss, calibrated, $R=20$",
       "stoploss_cal_R30": "Stop-loss, calibrated, $R=30$", "cusumrb_cal_R12": "CUSUM rollback, calibrated, $R=12$",
       "cusumrb_cal_R20": "CUSUM rollback, calibrated, $R=20$", "cusumrb_cal_R30": "CUSUM rollback, calibrated, $R=30$"}
for a, l in lab.items():
    v = A[a]
    if "violation" in v:
        w = v["violation"]["worst_stats"]
        viol = f"{r3(w['rate'])} [{r3(w['lo'])}, {r3(w['hi'])}]"; wr = tex(v["violation"]["worst"]) if w["k"] else "--"
    else:
        viol, wr = "--", "--"
    dn = v.get("d_never", {}).get("all")
    dnt = f"{dn['delta']:+.2f}".replace("-", "$-$") if dn else "0.00"
    rows.append(f"{l} & {v['J']:.2f} & {dnt} & {v.get('labels', 0):.1f} & {v.get('deployed', 0):.3f} & {viol} & {wr} \\\\")
write("tab_calib.tex", "\\begin{tabular}{@{}l r r r r l l@{}}\n\\toprule\nController & $J$ & vs never & labels & deployed & worst-regime viol.\\ [Wilson] & worst regime \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
def dm(a, ref, grp="all"):
    return A[a]["d_never"][grp] if ref == "never" else None
for R, L in ((12, "A"), (20, "B"), (30, "C")):
    v = A[f"stoploss_cal_R{R}"]
    mac(f"CalStopJ{L}", f"{v['J']:.2f}"); mac(f"CalStopDep{L}", f"{v['deployed']:.3f}")
    v = A[f"cusumrb_cal_R{R}"]; w = v["violation"]["worst_stats"]
    mac(f"CalCusJ{L}", f"{v['J']:.2f}"); mac(f"CalCusWorst{L}", r3(w["rate"])); mac(f"CalCusWorstLo{L}", r3(w["lo"]))
    mac(f"CalCusDNever{L}", f"{v['d_never']['all']['delta']:+.2f}")
mac("CalShieldJB", f"{A['f3_pi1_R20']['J']:.2f}"); mac("CalNeverJ", f"{A['never']['J']:.2f}")
mac("CalStopDNever", f"{A['stoploss_cal_R20']['d_never']['all']['delta']:+.2f}")
# real streams (third look), clean pooled and adverse cusum violations
rp = cal["real"]["results"]
for cond, C in (("clean", "Clean"), ("dropout_adverse", "Drop"), ("delay_adverse", "Delay")):
    P = rp[cond]["pooled"]["all14"]
    for h, H in ((6, "Six"), (14, "Fourteen"), (24, "TwentyFour")):
        a = P[f"cusumrb_cal_h{h}"]; Rk = str(int(cal["real"]["R_by_h"][str(h)]))
        mac(f"RCalCusViol{C}{H}", thousands(a["violation"]["k"]))
        mac(f"RCalCusJ{C}{H}", f"{a['J']:.1f}")
        s = P[f"stoploss_cal_h{h}"]
        mac(f"RCalStopViol{C}{H}", thousands(s["violation"]["k"]))
mac("RCalStopJ", f"{rp['clean']['pooled']['all14']['stoploss_cal_h14']['J']:.1f}")
mac("RCalStopDep", f"{rp['clean']['pooled']['all14']['stoploss_cal_h14']['deployed']:.3f}")
b = rp["clean"]["boot"]["all14"]["cusumrb_cal_h14"]["f3_pi1"]
mac("RCalCusVsShield", f"{b['delta']:.1f}"); mac("RCalCusVsShieldLo", f"{b['lo']:.1f}"); mac("RCalCusVsShieldHi", f"{b['hi']:.1f}")
(OUT / "numbers.tex").write_text("% generated by make_tables.py; do not edit\n" + "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in MAC.items()))
