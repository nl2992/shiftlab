"""Regenerate the 39-dataset table (Table real35) from the Phase 4b-10 result files.

Usage:  python3 paper/p4_tmlr/make_tables.py            # writes paper/p4_tmlr/tables/real35_rows.tex
        python3 paper/p4_tmlr/make_tables.py --write    # rewrites the marked block in main.tex
        python3 paper/p4_tmlr/make_tables.py --check    # diffs the rows against main.tex

Rule (as in REAL_CHAINS.md): a dataset is listed with its best positive stream, i.e. the orientation with the
largest rho_Gamma over the evaluated (T, B) cells; r1, the cell and the i.i.d.-optimal causal risk are read from
that stream's record. If the positive orientations disagree on the risk in the best cell, the range is shown.
"""
import glob
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parents[1] / "docs/paper4_continuation/rbdp/real_data/results"

TEXTS = [("en", "English"), ("fr", "French"), ("de", "German"), ("es", "Spanish"), ("it", "Italian"),
         ("pt", "Portuguese"), ("nl", "Dutch"), ("sv", "Swedish"), ("da", "Danish"), ("fi", "Finnish"),
         ("hu", "Hungarian"), ("pl", "Polish"), ("cs", "Czech"), ("la", "Latin"), ("ro", "Romanian"),
         ("ca", "Catalan"), ("eo", "Esperanto"), ("cy", "Welsh")]
# Phase 10c languages (family E); E:lang/fy/retry is positive by the evaluator but excluded (English translation), so absent.
TEXTS_10C = [("E:lang/af", "Afrikaans"), ("E:lang/br", "Breton"), ("E:lang/gl/retry", "Galician"),
             ("E:lang/ia/retry", "Interlingua"), ("E:lang/et/retry", "Estonian")]
ORDER = (
    [(f"T:{k}|L:{k}|L2:{k}", n, "text") for k, n in TEXTS]
    + [(i, n, "text") for i, n in TEXTS_10C]
    + [("S:P15502", "Elastin, human", "protein"), ("S:P04985", "Elastin, bovine", "protein"),
       ("S3:P07916", "Elastin, chicken", "protein"), ("S3:P11547", "Elastin, sheep", "protein"),
       ("S2:P46804", "Spidroin-2", "protein")]
    + [("F:faithful", "faithful, waiting $>70$", "geyser"), ("F:geyser", "geyser, waiting $>70$", "geyser"),
       ("D:geyser/Old_Faithful", "Old Faithful, 2020 on, interval $>$ median", "geyser"),
       ("D:geyser/Grand", "Grand geyser, interval $>$ median", "geyser")]
    + [("A:atlas_v2/openml_ldpa", "openml\\_ldpa", "promotion"), ("A:sprint_fresh/appliances", "appliances", "promotion"),
       ("A:sprint_fresh/beijing_pm25", "beijing\\_pm25", "promotion"),
       ("A:screen100/FOREX_audsgd-hour-Close", "FOREX aud/sgd", "promotion"),
       ("A:screen100/elec_MT_005", "electricity MT\\_005", "promotion"),
       ("A:screen100/elec_MT_010", "electricity MT\\_010", "promotion"),
       ("A:screen100/elec_MT_029", "electricity MT\\_029", "promotion"),
       ("A:screen100/pm_Shanghai", "PM2.5 Shanghai", "promotion"),
       ("A:screen100/pm_Shenyang", "PM2.5 Shenyang", "promotion"),
       ("A:screen100/tetouan_z1", "Tetouan power, zone 1", "promotion"),
       ("B:covtype", "covtype", "promotion"), ("Bext:electricity", "Elec2 (NSW electricity)", "promotion")]
)


def load_positive():
    out = {}
    for f in sorted(glob.glob(str(RES / "attempts*.jsonl"))):
        for line in open(f):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict) or not isinstance(rec.get("streams"), list):
                continue
            for st in rec["streams"]:
                if isinstance(st, dict) and st.get("positive") and st.get("best_good_cell"):
                    out.setdefault(rec["id"], []).append(st)
    return out


def fmt_risk(vals):
    vals = sorted(set(round(v, 3) for v in vals))
    g = lambda v: f"{v:.3f}".rstrip("0").rstrip(".")
    return g(vals[0]) if len(vals) == 1 else f"{g(vals[0])}--{g(vals[-1])}"


def rows():
    pos = load_positive()
    lines, last = [], None
    for ids, name, kind in ORDER:
        sts = [s for i in ids.split("|") for s in pos.get(i, [])]
        if not sts:
            raise SystemExit(f"no positive stream for {ids}")
        best = max(sts, key=lambda s: s["best_good_cell"]["rho_Gamma"])
        c = best["best_good_cell"]
        risks = [cell["risk_causal_of_iid_policy"] for s in [best] for cell in s["cells"]
                 if (cell["T"], cell["B"]) == (c["T"], c["B"])]
        if last and kind != last:
            lines.append("\\midrule")
        last = kind
        lines.append(f"{name} & {kind} & {best['n']} & ${best['r1']:+.3f}$ & {c['rho_Gamma']:.3f} "
                     f"(T{c['T']} B{c['B']}) & {fmt_risk(risks)}\\\\".replace("$+", "$+").replace("$-", "$-"))
    return lines


if __name__ == "__main__":
    out = HERE / "tables"
    out.mkdir(exist_ok=True)
    lines = rows()
    (out / "real35_rows.tex").write_text("\n".join(lines) + "\n")
    print(f"wrote {out / 'real35_rows.tex'} ({sum(1 for l in lines if l != chr(92) + 'midrule')} datasets)")
    if "--write" in sys.argv:
        tex = (HERE / "main.tex").read_text()
        a, b = tex.index("% BEGIN real35"), tex.index("% END real35")
        head = tex[:a].rsplit("\n", 1)[0] + "\n"
        new = head + "% BEGIN real35 (generated by make_tables.py --write)\n" + "\n".join(lines) + "\n" + tex[b:]
        (HERE / "main.tex").write_text(new)
        print("updated table block in main.tex")
    if "--check" in sys.argv:
        tex = (HERE / "main.tex").read_text()
        norm = lambda s: re.sub(r"\s+", "", s.replace("$-", "$−"))
        bad = 0
        for l in lines:
            if l == "\\midrule":
                continue
            key = l.split("&")[0].strip()
            hand = next((h for h in tex.splitlines() if h.startswith(key + " &")), None)
            if hand is None or norm(hand) != norm(l):
                bad += 1
                print("DIFF\n  gen :", l, "\n  hand:", hand)
        print("rows differing from main.tex:", bad)
