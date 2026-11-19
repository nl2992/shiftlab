"""Phase 5 (PROTOCOL.md Addendum E): diverse supporting datasets until the total positive count is 20.

Usage: PYTHONPATH=src uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/run_phase5.py [--smoke]
--smoke parses/fetches one item per family and prints stream summaries without running the solver.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import run_phase4b as p4b  # noqa: E402

RAW = ROOT / "data/raw/real_chains/phase5"
RES = ROOT / "docs/paper4_continuation/rbdp/real_data/results"
OUT = RES / "attempts_phase5.jsonl"
LOG = RES / "phase5_run.log"
MANIFEST = RAW / "SOURCE_manifest.jsonl"
SEED = 20261117
TARGET, START = 20, 10
SMOKE = "--smoke" in sys.argv
FAO_URL = "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
UNIPROT = "https://rest.uniprot.org/uniprotkb/search"
UQ = ('(protein_name:fibroin OR protein_name:spidroin OR protein_name:elastin OR protein_name:"silk protein") '
      "AND reviewed:true AND length:[600 TO *]")
HYDRO = set("IVLFCMA")
CROPS = [("olive", ["Olives"]), ("pistachio", ["Pistachios; in shell", "Pistachios, in shell"]),
         ("pecan", ["Pecan nuts", "Pecans; in shell", "Pecans, in shell"]), ("apple", ["Apples"]),
         ("avocado", ["Avocados"]), ("mango", ["Mangoes; guavas and mangosteens", "Mangoes, guavas and mangosteens"])]
LANGS = "hu pl cs la ru el ro ca eo tr".split()


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(LOG, "a") as f:
        f.write(s + "\n")


def manifest(url: str, data: bytes) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "a") as f:
        f.write(json.dumps({"url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                            "time": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")


def curl(url: str, dest: Path, params: dict | None = None, timeout: int = 120) -> bytes | None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["curl", "-sS", "-f", "-m", str(timeout), "-o", str(dest)]
    if params:
        cmd += ["-G"] + [a for k, v in params.items() for a in ("--data-urlencode", f"{k}={v}")]
    r = subprocess.run(cmd + [url], capture_output=True)
    if r.returncode != 0 or not dest.exists():
        return None
    data = dest.read_bytes()
    manifest(url + ("?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else ""), data)
    return data


def done_ids() -> set:
    return {json.loads(line)["id"] for line in open(OUT)} if OUT.exists() else set()


def tally() -> int:
    n = START
    if OUT.exists():
        n += sum(bool(json.loads(line).get("positive")) and json.loads(line).get("counts", True) for line in open(OUT))
    return n


def emit(rec: dict) -> None:
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n")


def eval_streams(cid: str, streams: list[tuple[str, np.ndarray]]) -> dict:
    """Evaluate each stream with the Phase 4b evaluator plus the shuffle control; dataset positive if any stream is."""
    rec = {"status": "evaluated", "streams": []}
    for orient, x in streams:
        x = np.asarray(x, int)
        if x.std() == 0:
            rec["streams"].append({"orientation": orient, "n": len(x), "positive": False, "note": "constant stream"})
            continue
        r = p4b.evaluate(x, f"{cid}_{orient}")
        r["orientation"] = orient
        if r["positive"]:
            rng = np.random.default_rng(SEED)
            sh = []
            for k in range(5):
                rs = p4b.evaluate(rng.permutation(x), f"{cid}_{orient}_shuf{k}")
                sh.append({"positive": rs["positive"], "g1_iid_ok": rs["g1_iid_ok"], "r1": rs["r1"]})
            r["shuffles"] = sh
            r["positive"] = sum(s["positive"] for s in sh) <= 1
        rec["streams"].append(r)
        log(cid, orient, "n", r["n"], "r1 %.3f" % r["r1"], "pos", r["positive"], r["best_good_cell"])
    rec["positive"] = any(s["positive"] for s in rec["streams"])
    return rec


def both(x):
    x = np.asarray(x, int)
    return [("x=1", x), ("1-x", 1 - x)]


# ---------------------------------------------------------------- Family F
def family_F():
    base = ROOT / "data/raw/real_chains"
    spec = {"F:faithful": [("eruptions>3", "c01_faithful"), ("waiting>70", "p23_faithful_waiting")],
            "F:geyser": [("duration>3", "c02_geyser"), ("waiting>70", "p24_geyser_waiting")]}
    for cid, vars_ in spec.items():
        streams = []
        for vname, d in vars_:
            x = np.loadtxt(base / d / "stream.csv", skiprows=1, dtype=int)
            streams += [(f"{vname}|{o}", s) for o, s in both(x)]
        yield cid, {"family": "F", "source": "cached Rdatasets (Phases 1-2)"}, streams


# ---------------------------------------------------------------- Family S
def family_S():
    data = curl(UNIPROT, RAW / "uniprot_structural.fasta", {"query": UQ, "format": "fasta", "size": "100"})
    if data is None:
        yield "S:fetch", {"family": "S", "status": "fetch failed", "source": UNIPROT}, None
        return
    seen, entries = set(), []
    for blk in data.decode().split(">")[1:]:
        head, *seq = blk.split("\n")
        m = re.match(r"(\S+)\s+(.*?)\s+OS=(.*?)\s+OX=", head)
        if not m:
            continue
        acc, name, org = m.group(1).split("|")[1], m.group(2), m.group(3)
        if (name, org) in seen:
            continue
        seen.add((name, org))
        entries.append((acc, name, org, "".join(seq)))
        if len(entries) == 12:
            break
    for acc, name, org, s in entries:
        s = s[:3000]
        x = np.array([1 if c in HYDRO else 0 for c in s])
        yield f"S:{acc}", {"family": "S", "name": name, "organism": org, "length_used": len(s)}, both(x)


# ---------------------------------------------------------------- Family Y
def moving_median_stream(y):
    y = np.asarray(y, float)
    n = len(y)
    med = np.array([np.median(y[i - 2:i + 3]) for i in range(2, n - 2)])
    return (y[2:n - 2] > med).astype(int)


def load_fao():
    zp = RAW / "fao/fao.zip"
    if not zp.exists():
        log("downloading FAOSTAT bulk (~34 MB)")
        if curl(FAO_URL, zp, timeout=600) is None:
            return None
    else:
        manifest(FAO_URL + " (cached)", zp.read_bytes())
    prod, yld = {}, {}
    with zipfile.ZipFile(zp) as z:
        nm = next(n for n in z.namelist() if "Normalized" in n)
        with z.open(nm) as fh:
            for row in csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8")):
                if int(row["Area Code"]) >= 5000:
                    continue
                el = row["Element Code"]
                if el not in ("5510", "5412"):
                    continue
                v = row["Value"]
                if v == "":
                    continue
                key = (row["Item"], row["Area"])
                (prod if el == "5510" else yld).setdefault(key, {})[int(row["Year"])] = float(v)
    return prod, yld


def noise_control(n_raw: int):
    rng = np.random.default_rng(SEED)
    res = []
    for i in range(24):
        x = moving_median_stream(rng.standard_normal(n_raw))
        rec = eval_streams(f"Y:noise{i}", both(x))
        res.append({"i": i, "n": len(x), "positive": rec["positive"]})
    return res


def family_Y():
    fao = load_fao()
    if fao is None:
        yield "Y:fetch", {"family": "Y", "status": "fetch failed", "source": FAO_URL}, None
        return
    prod, yld = fao
    items = []
    for crop, names in CROPS:
        nm = next((n for n in names if any(k[0] == n for k in prod)), None)
        if nm is None:
            items.append((crop, None, None))
            continue
        top = sorted(((p.get(2020, 0), k[1]) for k, p in prod.items() if k[0] == nm and k[1] != "China"), reverse=True)[:3]
        for _, country in top:
            items.append((crop, nm, country))
    # noise control first (family counts only if <= 1 of 24 noise series qualify)
    n_raw = max(len(yld[(nm, c)]) for _, nm, c in items if nm)
    prev = [json.loads(line) for line in open(OUT)] if OUT.exists() else []
    prev = [r for r in prev if r["id"] == "Y:noise_control"]
    if prev:
        ok = prev[0]["family_counts"]
    elif not SMOKE:
        if tally() >= TARGET:
            return
        ctrl = noise_control(n_raw)
        nq = sum(c["positive"] for c in ctrl)
        ok = nq <= 1
        emit({"id": "Y:noise_control", "family": "Y", "status": "noise control", "n_series": 24, "n_raw": n_raw,
              "n_qualify": nq, "family_counts": ok, "series": ctrl, "positive": False})
        log("Y noise control:", nq, "of 24 qualify; family counts:", ok)
    else:
        ok = True
    for crop, nm, country in items:
        if nm is None:
            yield f"Y:{crop}", {"family": "Y", "status": "no FAOSTAT item", "crop": crop}, None
            continue
        series = yld.get((nm, country), {})
        yrs = sorted(y for y in series if y >= 1961)
        while yrs and yrs[-1] - yrs[0] + 1 != len(yrs):  # keep the last contiguous run
            k = max(i for i in range(1, len(yrs)) if yrs[i] - yrs[i - 1] > 1)
            yrs = yrs[k:]
        if len(yrs) < 30:
            yield f"Y:{crop}:{country}", {"family": "Y", "status": "too few years", "crop": crop, "country": country}, None
            continue
        x = moving_median_stream([series[y] for y in yrs])
        extra = {"family": "Y", "crop": crop, "country": country, "item": nm, "years": [yrs[0], yrs[-1]],
                 "counts": ok, "family_counts_flag": ok}
        if not ok:
            yield f"Y:{crop}:{country}", {**extra, "status": "family void (noise control)"}, None
        else:
            yield f"Y:{crop}:{country}", extra, both(x)


# ---------------------------------------------------------------- Family L
def fetch_book(book_id: int):
    for url in p4b.mirror_urls(book_id):
        dest = RAW / f"texts/{book_id}.txt"
        data = curl(url, dest, timeout=90)
        if data and 1000 < len(data) < 6_000_000:
            return data.decode("utf-8", errors="ignore"), url
    return None, "all mirror paths failed"


def family_L():
    cands = {c["key"]: c for c in json.load(open(RES / "phase4_candidates.json"))["items"] if c["family"] == "T"}
    for lang in LANGS:
        c = cands[lang]
        bid = (c.get("resolved") or {}).get("book_id")
        base = {"family": "L", "lang": lang, "book_id": bid}
        if not bid:
            yield f"L:{lang}", {**base, "status": "fetch failed", "note": "no book id resolved"}, None
            continue
        text, src = fetch_book(int(bid))
        base["source"] = src
        if text is None:
            yield f"L:{lang}", {**base, "status": "fetch failed"}, None
            continue
        vowels = set(c["vowels"])
        if lang == "ru":
            def ok(ch):
                return "Ѐ" <= ch <= "ӿ"
        elif lang == "el":
            def ok(ch):
                return "Ͱ" <= ch <= "Ͽ" or "ἀ" <= ch <= "῿"
        else:
            def ok(ch, vowels=vowels):
                return ch.isascii() or ch in vowels or ch.isalpha() and ord(ch) < 0x0250
        L = p4b.letters(text, ok)
        if len(L) < 1000:
            yield f"L:{lang}", {**base, "status": f"too few letters ({len(L)})"}, None
            continue
        xv = np.array([1 if ch in vowels else 0 for ch in L])
        yield f"L:{lang}", base, [("vowel=1", xv), ("consonant=1", 1 - xv)]


def main():
    RES.mkdir(parents=True, exist_ok=True)
    done = done_ids()
    for fam in (family_F, family_S, family_Y, family_L):
        for cid, meta, streams in fam():
            if SMOKE:
                print(cid, meta, None if streams is None else [(o, len(x), int(np.sum(x)), round(float(np.corrcoef(x[:-1], x[1:])[0, 1]), 3)) for o, x in streams], flush=True)
                continue
            if cid in done:
                continue
            if tally() >= TARGET:
                log("TARGET reached; stopping")
                return
            rec = {"id": cid, **meta}
            if streams is None:
                rec.setdefault("status", "fetch failed")
                rec["positive"] = False
            else:
                rec.update(eval_streams(cid, streams))
            if rec.get("family") == "Y" and rec.get("counts") is False:
                rec["positive"] = False
            emit(rec)
            log("DONE", cid, rec.get("status"), "positive", rec.get("positive"), "TALLY", tally())
    log("lists exhausted; final tally", tally())


if __name__ == "__main__":
    main()
