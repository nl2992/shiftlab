"""Phase 4 (Addendum C): level streams (text vowels, DNA R/Y and S/W). Usage: run_phase4.py resolve | run
`resolve` writes results/phase4_candidates.json (before any fit). `run` processes candidates in order, resumable,
stops at 10 qualifying distinct datasets.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evaluate as ev  # noqa: E402
import fetch_phase4 as f4  # noqa: E402
import run_phase3 as p3  # noqa: E402

ROOT = HERE.parents[3]
RES = ROOT / "docs/paper4_continuation/rbdp/real_data/results"
CANDS = RES / "phase4_candidates.json"
ATT = RES / "attempts_phase4.jsonl"
TARGET = 10
SEED0 = 20261117


def resolve():
    f4.RAW.mkdir(parents=True, exist_ok=True)
    items = []
    texts = {}
    for lang in f4.LANGS:
        texts[lang] = f4.resolve_text(lang)
        print(lang, texts[lang].get("book_id"), texts[lang].get("error"), flush=True)
        time.sleep(0.5)
    for fam, key in f4.order():
        if fam == "T":
            items.append(dict(family="T", key=key, resolved=texts[key], vowels="".join(sorted(f4.vowels_of(key))),
                              script=f4.script_of(key)))
        else:
            items.append(dict(family="G", key=key, url_template="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
                              "db=nuccore&id=<acc>&rettype=fasta&retmode=text&seq_start=1001&seq_stop=4000"))
    CANDS.write_text(json.dumps(dict(order=[f"{i['family']}:{i['key']}" for i in items], items=items), indent=1, ensure_ascii=False))
    print(len(items), "candidates;", sum(1 for t in texts.values() if not t["ok"]), "text resolution failures")


def shuffles(x, sp_ok):
    out = []
    for k in range(5):
        rng = np.random.default_rng(SEED0 + k)
        r = p3.eval_stream(rng.permutation(x), f"shuffle{k}")
        out.append(dict(k=k, seed=SEED0 + k, g1_pass=r["g1"]["pass_"], g2_pass=r["g2"]["pass_"],
                        positive_any_cell=r["positive_any_cell"], nondegenerate_positive=r["nondegenerate_positive"],
                        rho_max=r.get("rho_max"), fit={a: r["fit"][a] for a in ("t01", "t10", "e0", "e1")},
                        runtime_s=r["runtime_s"]))
    return out


def eval_one(x, tag):
    x = np.asarray(x, int)
    s = dict(tag=tag, n=int(len(x)), n_ones=int(x.sum()), r1=p3.lag1(x))
    if not (s["r1"] == s["r1"] and s["r1"] <= p3.R1_CUT):
        s.update(screened_out=True)
        return s
    rec = p3.eval_stream(x, tag)
    rec.update(s)
    rec["screened_out"] = False
    rec["qualifies"] = False
    if rec["nondegenerate_positive"]:
        rec["cells_d2"] = ev.eval_chain(rec["solver_params"], delay1=False, delay2=True, log=lambda *_: None)
        sh = shuffles(x, True)
        rec["shuffles"] = sh
        rec["shuffle_g1_passes"] = sum(r["g1_pass"] for r in sh)
        rec["shuffle_positives"] = sum(r["nondegenerate_positive"] for r in sh)
        rec["qualifies"] = bool(rec["shuffle_positives"] <= 1)
    return rec


def main():
    cands = json.loads(CANDS.read_text())["items"]
    done = {}
    if ATT.exists():
        for line in ATT.read_text().splitlines():
            r = json.loads(line)
            done[r["seq"]] = r
    for seq, c in enumerate(cands, start=1):
        if sum(r.get("dataset_qualifies", False) for r in done.values()) >= TARGET:
            print("10 qualifying datasets reached; stopping")
            break
        if seq in done:
            continue
        t0 = time.perf_counter()
        name = f"{c['family']}:{c['key']}"
        rec = dict(seq=seq, family=c["family"], key=c["key"], name=name, started=time.strftime("%Y-%m-%dT%H:%M:%S"))
        print(f"[{seq}] {name}", flush=True)
        try:
            if c["family"] == "T":
                if not c["resolved"]["ok"]:
                    raise RuntimeError(c["resolved"]["error"])
                x, meta = f4.fetch_text(c["key"], c["resolved"])
                streams = {"vowel": x}
                rec["book"] = dict(id=c["resolved"]["book_id"], title=c["resolved"]["title"])
            else:
                streams, meta = f4.fetch_dna(c["key"])
            rec["fetch"] = dict(ok=True, **meta)
        except Exception as ex:  # noqa: BLE001
            rec.update(fetch=dict(ok=False, error=f"{type(ex).__name__}: {ex}"), outcome="fetch failed", dataset_qualifies=False)
            _write(rec, seq, done)
            continue
        rec["streams"] = {}
        for sname, x in streams.items():
            r = eval_one(x, f"{name}:{sname}")
            rec["streams"][sname] = r
            if not r["screened_out"]:
                (RES / f"s{seq:02d}_{c['family']}_{c['key']}_{sname}.json").write_text(json.dumps(r, indent=1, default=str))
        rec["dataset_qualifies"] = any(r.get("qualifies") for r in rec["streams"].values())
        rec["outcome"] = ("qualifies" if rec["dataset_qualifies"] else
                          "evaluated, not qualifying" if any(not r["screened_out"] for r in rec["streams"].values())
                          else "screened out")
        rec["runtime_s"] = time.perf_counter() - t0
        _write(rec, seq, done)
    print("DONE")


def _write(rec, seq, done):
    with open(ATT, "a") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    done[seq] = rec
    print("   ->", rec["outcome"], {k: round(v["r1"], 3) for k, v in rec.get("streams", {}).items()},
          "| qualifying datasets:", sum(r.get("dataset_qualifies", False) for r in done.values()), flush=True)


if __name__ == "__main__":
    {"resolve": resolve, "run": main}[sys.argv[1]]()
