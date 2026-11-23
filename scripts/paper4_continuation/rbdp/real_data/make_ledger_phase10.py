"""Regenerate LEDGER_PHASE10.md from the Phase 10, 10b and 10c attempt records. Read-only on the records."""
import glob
import json
from pathlib import Path

RD = Path(__file__).resolve().parents[4] / "docs/paper4_continuation/rbdp/real_data"
RES = RD / "results"
OUT = RD / "LEDGER_PHASE10.md"
MIN_N = 200

# Reasons and sources from PHASE10_PROTOCOL.md / run_phase10.py, used when the record has none.
REASON = {
    "B:covtype": "spatially ordered cover-type map; slow covariate drift along the ordering",
    "B:poker": "synthetic card hands, no temporal structure; expected null (negative control for the premium)",
    "B:kdd99_10pct": "network intrusion; bursty attack regimes, abrupt drift",
    "B:intel_sensor": "sensor-network time series; smooth diurnal drift",
    "B:ozone": "environmental measurements, small n; seasonal drift",
    "B:INSECTS": "drift benchmark with gradual, abrupt and recurring drift; hosted on a Google Drive share",
    "Bext:electricity": "energy; New South Wales electricity prices",
    "Bext:Bike_Sharing_Demand": "demand; hourly bike rentals",
    "Bext:MagicTelescope": "physics; iid, expected null",
    "Bext:Higgs": "physics; iid, expected null (first 200k rows)",
    "Bext:PhishingWebsites": "web security",
    "Bext:SMSSpam": "text; spam filtering of SMS messages",
    "Bext:adult": "census",
    "Bext:bank-marketing": "finance; bank marketing campaigns",
    "Bext:default-of-credit-card-clients": "finance; credit card default",
    "Bext:OnlineNewsPopularity": "news popularity over time",
    "Bext:occupancy": "building sensors",
    "Bext:gas-drift": "gas-sensor drift",
}
NULL_CONTROLS = {"B:poker", "C:jannis", "Bext:MagicTelescope", "Bext:Higgs"}
OPENML_NAME = lambda n: f"OpenML name={n} v1 (sklearn fetch_openml)"
SOURCE = {
    "B:covtype": "UCI covtype.data.gz",
    "B:poker": "UCI poker-hand training+testing",
    "B:kdd99_10pct": "figshare kddcup99 10% (fetch failed; see retry)",
    "B:intel_sensor": "db.csail.mit.edu/labdata/data.txt.gz (Intel Berkeley)",
    "B:ozone": "UCI ozone eighthr.data",
    "B:INSECTS": "Google Drive share (not fetched)",
}
FAMILY_TITLE = {"B": "Family B: standard drift benchmarks", "Bext": "Family Bext: OpenML benchmarks",
                "C": "Family C: further OpenML sources", "D": "Family D (Phase 10b): alternation sources",
                "E": "Family E (Phase 10c): more diverse sources"}
# A retry that the registered rule evaluated but that must not be counted, with the reason written into the outcome.
EXCLUDED = {"E:lang/fy/retry": "excluded: selected book is an English translation (language tag fy), so the stream is not Frisian; "
            "rule applied as registered"}


def load():
    recs, notes = {}, {}
    for f in sorted(glob.glob(str(RES / "attempts_phase10_shard*.jsonl"))):
        for line in open(f):
            d = json.loads(line)
            recs[d["id"]] = d
    for line in open(RES / "attempts_phase10_retry.jsonl"):
        d = json.loads(line)
        old = recs.get(d["id"])
        if old is not None and old["status"] == "fetch failed":
            notes[d["id"]] = "original run: fetch failed" + (f" ({old['error'][:80]})" if old.get("error") else "")
        recs[d["id"]] = d
    for line in open(RES / "attempts_phase10b.jsonl"):
        d = json.loads(line)
        recs[d["id"]] = d
    # Phase 10c: a retry record supersedes the fetch-failed record of the same language (matched by retry_of / language code).
    c = {}
    for line in open(RES / "attempts_phase10c.jsonl"):
        d = json.loads(line)
        c[d["id"]] = d
    for line in open(RES / "attempts_phase10c_retry.jsonl"):
        d = json.loads(line)
        old = c.get(d["retry_of"])
        assert old is not None and old["status"] == "fetch failed" and old["id"].split("/")[-1] == d["id"].split("/")[-2]
        notes[d["id"]] = "original run: fetch failed" + (f" ({old['error'][:80]})" if old.get("error") else "")
        del c[old["id"]]
        c[d["id"]] = d
    recs.update(c)
    return recs, notes


def short_err(e):
    import re
    e = (e or "").replace("|", "/").replace("\n", " ")
    m = re.search(r"error: (\d{3})|HTTPError (\d{3})", e)
    if m:
        return "HTTP " + (m.group(1) or m.group(2))
    return e[:90] or "no error recorded"


def best_positive_stream(d):
    ps = [s for s in d.get("streams", []) if s.get("positive")]
    return max(ps, key=lambda s: s["best_good_cell"]["rho_Gamma"]) if ps else None


def classify(d):
    """Return (category, outcome text). Categories: positive, null, short, rejected, unavailable, phase4."""
    st = d["status"]
    if d["id"] in EXCLUDED:
        return "excluded", EXCLUDED[d["id"]]
    if st.startswith("already evaluated"):
        return "phase4", "already evaluated in Phase 4 (family G, 16 genomes); not repeated"
    if st == "fetch failed" and d["id"] == "B:INSECTS":
        return "unavailable", "source unavailable: hosted on a Google Drive share, not fetched"
    if st == "fetch failed":
        e = short_err(d.get("error"))
        return "unavailable", "source unavailable: " + (e + " from the Gutenberg catalog" if e == "HTTP 503" else e)
    if st.startswith("too short"):
        return "short", f"too few disagreement rounds ({d.get('n', 0)} < {MIN_N})"
    streams = d["streams"]
    if d["positive"]:
        b = best_positive_stream(d)
        c = b["best_good_cell"]
        nsh = sum(s["positive"] for s in b["shuffles"])
        return "positive", f"supports (premium {c['rho_Gamma']:.3f} at T={c['T']}, B={c['B']}, {nsh}/5 shuffles)"
    r1 = streams[0]["r1"]
    passing = [s for s in streams if s.get("g1_iid_ok") and s.get("g2")]
    if not passing:
        g1_fail = not any(s.get("g1_iid_ok") for s in streams)
        g2_fail = not any(s.get("g2") for s in streams)
        if g2_fail and g1_fail:
            txt = "two-state fit rejected (G2); also G1 failed (no gain over i.i.d. by BIC)"
        elif g2_fail:
            txt = "two-state fit rejected (G2)"
        elif g1_fail:
            txt = "G1 failed (structured model does not beat i.i.d. by BIC)"
        else:
            txt = "no stream passes both G1 and G2"
        return "rejected", f"{txt}; r1 {r1:.3f}"
    if abs(r1) < 0.1:
        return "null", f"near-i.i.d. stream (r1 {r1:.3f}): zero premium, as the theory predicts"
    if r1 >= 0.1:
        return "null", f"persistent chain, no premium in evaluated cells (r1 {r1:.3f})"
    return "null", f"alternating chain (r1 {r1:.3f}), no premium in evaluated cells"


def row(d, notes):
    cat, outcome = classify(d)
    i = d["id"]
    if i in NULL_CONTROLS and cat in ("null", "rejected", "short"):
        outcome += " (negative control, null expected)"
    elif i in NULL_CONTROLS:
        outcome += " (listed as a null-expected control)"
    streams = d.get("streams") or []
    n = d.get("n") if d.get("n") is not None else (streams[0]["n"] if streams else "")
    r1 = f"{streams[0]['r1']:.3f}" if streams else ""
    best, cell = "", ""
    b = best_positive_stream(d)
    if b:
        c = b["best_good_cell"]
        best, cell = f"{c['rho_Gamma']:.3f}", f"T={c['T']}, B={c['B']}"
    src = d.get("source") or SOURCE.get(i) or OPENML_NAME(d["name"])
    if i.startswith("E:lang") and not isinstance(src, dict) and src.startswith("OpenML"):
        src = f"https://gutendex.com/books/?languages={i.split('/')[1]}&sort=popular"
    if isinstance(src, dict):
        src = f"Project Gutenberg ebook {src['ebook_id']} ({d['title']}); {src['url']}"
    elif d.get("book_id"):
        src = f"Project Gutenberg ebook {d['book_id']} ({d['title']}); {d['source_text']}"
    reason = d.get("reason") or REASON.get(i, "")
    status = d["status"]
    if i in notes:
        status += f"; retry superseded: {notes[i]}"
    elif d.get("retry_of"):
        status += " (retry of fetch failure)"
    pos = ("yes (evaluator; not counted)" if cat == "excluded" else "yes") if d["positive"] else "no"
    cells = [i, src, reason, status, str(n), r1, pos, best, cell, outcome]
    return cat, "| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in cells) + " |"


def main():
    recs, notes = load()
    rows = {}
    for d in recs.values():
        cat, line = row(d, notes)
        rows.setdefault(d["family"], []).append((cat, line))
    allc = [c for v in rows.values() for c, _ in v]
    cnt = {k: allc.count(k) for k in ("positive", "excluded", "null", "short", "rejected", "unavailable", "phase4")}
    total = len(allc)
    assert sum(cnt.values()) == total

    L = ["# Phase 10, 10b and 10c ledger", "",
         "Phase 10 adds benchmark families B, Bext and C. Phase 10b adds family D, sources with a known alternation "
         "mechanism. Phase 10c adds family E: geysers, tennis points, collagen proteins, cricket and 13 further languages "
         "(protocol in `PHASE10_PROTOCOL.md`). All three use the Phase 7 pipeline, shuffle control and orientation handling; the positivity rule is "
         "unchanged (two-state fit passes G1 and G2, a positive premium in some (T, B) cell, and the shuffle control "
         "in `run_phase5.eval_streams`, which allows at most 1 of 5 positive shuffles; every positive below has 0/5). "
         "Non-positive datasets are listed with the reason and are not added to the paper.", "",
         "Records live in `results/attempts_phase10_shard{0..3}.jsonl`, `results/attempts_phase10_retry.jsonl` "
         "(a retry record supersedes a shard record whose status was `fetch failed`; the original failure is noted in the "
         "status column), `results/attempts_phase10b.jsonl`, `results/attempts_phase10c.jsonl` and "
         "`results/attempts_phase10c_retry.jsonl` (a retry supersedes the fetch-failed record of the same language; a language "
         "is one dataset, counted once). A retry that the evaluator calls positive can still be excluded when the "
         "selected source is not what the row says (E:lang/fy/retry); it is listed, not counted. This file is generated by "
         "`scripts/paper4_continuation/rbdp/real_data/make_ledger_phase10.py`; do not edit by hand.", "",
         "## Counts", "",
         f"- Attempted: {total}",
         f"- Positive (supporting): {cnt['positive']}",
         f"- Positive by the evaluator but excluded: {cnt['excluded']}",
         f"- Evaluated, no premium (null): {cnt['null']}",
         f"- Too short: {cnt['short']}",
         f"- Fit rejected (G1 or G2): {cnt['rejected']}",
         f"- Source unavailable: {cnt['unavailable']}",
         f"- Already evaluated in Phase 4: {cnt['phase4']}", ""]
    hdr = ["| id | source | reason | status | n | r1 | positive | best rho_Gamma | cell | outcome reason |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for fam in ("B", "Bext", "C", "D", "E"):
        L += [f"## {FAMILY_TITLE[fam]} ({len(rows[fam])} rows)", ""] + hdr + [l for _, l in rows[fam]] + [""]
    L += ["## New supporting datasets", "",
          "Risk is the causal risk of the i.i.d.-optimal policy in the best cell (cells[*].risk_causal_of_iid_policy at "
          "the best (T, B)).", "",
          "| id | family | r1 | best rho_Gamma | cell (T, B) | i.i.d.-optimal policy causal risk | note |",
          "|---|---|---|---|---|---|---|"]
    for d in sorted(recs.values(), key=lambda d: d["id"]):
        b = best_positive_stream(d)
        if not b:
            continue
        c = b["best_good_cell"]
        risks = [x["risk_causal_of_iid_policy"] for x in b["cells"] if x["T"] == c["T"] and x["B"] == c["B"]]
        note = ""
        if d["family"] == "E" and d["id"].startswith("E:lang"):
            note = f"Gutenberg ebook {(d.get('source') or {}).get('ebook_id') if isinstance(d.get('source'), dict) else d['book_id']}"
        if d["id"] in EXCLUDED:
            continue
        if d["id"] == "D:geyser/Old_Faithful":
            note = ("replication: independent recent recording (2020 on) of a geyser already in the 35 "
                    "(the 1980s faithful/geyser R datasets)")
        elif d["id"] == "D:geyser/Grand":
            note = "new source"
        L.append(f"| {d['id']} | {d['family']} | {b['r1']:.3f} | {c['rho_Gamma']:.3f} | T={c['T']}, B={c['B']} | "
                 f"{risks[0]:.3f} | {note} |")
    L += ["", "Not counted: E:lang/fy/retry is positive by the evaluator (r1 "
          f"{recs['E:lang/fy/retry']['streams'][0]['r1']:.3f}), but the pre-registered most-popular rule selected ebook 40986, an English "
          "translation tagged fy, so the stream is English text. It is excluded; the rule is applied as registered and no other book is substituted.",
          "", "Still fetch failed (Gutenberg catalog HTTP 503 on retry, not evaluated): " +
          ", ".join(sorted(d["id"].split("/")[1] for d in recs.values() if d["family"] == "E" and classify(d)[0] == "unavailable")) + "."]
    OUT.write_text("\n".join(L) + "\n")
    print(cnt, total)


if __name__ == "__main__":
    main()
