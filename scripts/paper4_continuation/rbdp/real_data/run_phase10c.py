"""Phase 10c (PHASE10_PROTOCOL.md, section "Phase 10c"): family E, more diverse supporting sources.
Same evaluator, shuffle control and positivity rule as Phases 5-10b (run_phase5.eval_streams); no stopping target; every
outcome (positive, null, fetch failed) is recorded with the reason the source was chosen.

Usage: PYTHONPATH=src python scripts/paper4_continuation/rbdp/real_data/run_phase10c.py [--prepare] [--smoke] [--shard=k/n]
--prepare downloads the GeyserTimes files and fixes the geyser selection (run once, before the shards).
"""

from __future__ import annotations

import gzip
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
sys.path.insert(0, str(HERE))
import run_phase5 as p5  # noqa: E402

ROOT, RES = p5.ROOT, p5.RES
p5.RAW = ROOT / "data/raw/real_chains/phase10c"
p5.OUT = RES / "attempts_phase10c.jsonl"
p5.LOG = RES / "phase10c_run.log"
p5.MANIFEST = p5.RAW / "SOURCE_manifest.jsonl"
RAW = p5.RAW
SMOKE = "--smoke" in sys.argv
PREPARE = "--prepare" in sys.argv
SHARD = next((a.split("=")[1] for a in sys.argv if a.startswith("--shard=")), None)
CAP, MIN_N = 3000, 200
SEED = p5.SEED
GAP_FACTOR = 3.0


def fetch(url: str, name: str, timeout: int = 300, retries: int = 1):
    """Returns (bytes | None, error string). Cached under RAW/raw/; written atomically."""
    dest = RAW / "raw" / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest.read_bytes(), ""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + f".part{abs(hash((time.time(), name))) % 10**6}")
    err = ""
    for a in range(retries + 1):
        time.sleep(0.4)
        r = subprocess.run(["curl", "-sS", "-f", "-L", "-m", str(timeout), "-o", str(tmp), url], capture_output=True)
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            tmp.rename(dest)
            data = dest.read_bytes()
            p5.manifest(url, data)
            return data, ""
        err = (r.stderr.decode(errors="ignore").strip() or f"curl exit {r.returncode}")[:300]
        if tmp.exists():
            tmp.unlink()
        time.sleep(3)
    return None, err


def threshold_stream(v):
    v = np.asarray(v, float)
    return (v > np.median(v)).astype(int)


def _r1(x):
    return round(float(np.corrcoef(x[:-1], x[1:])[0, 1]), 3)


def wn_threshold(n: int):
    return _r1(threshold_stream(np.random.default_rng(SEED).standard_normal(n)))


def wn_bernoulli(n: int, p: float):
    return _r1((np.random.default_rng(SEED).random(n) < p).astype(int))


def summary(x):
    x = np.asarray(x, int)
    r1 = float(np.corrcoef(x[:-1], x[1:])[0, 1]) if x.std() > 0 else float("nan")
    return {"n": int(len(x)), "mean": round(float(x.mean()), 4), "r1": round(r1, 4)}


def finish(cid, meta, det, x):
    if len(x) < MIN_N:
        return cid, {**meta, **det, "status": f"too short ({len(x)})", "n": int(len(x))}, None
    return cid, {**meta, **det, **summary(x)}, p5.both(x)


# ---------------------------------------------------------------- E1: geysers
GT_BASE = "https://geysertimes.org/archive/"
GT_URL = GT_BASE + "geysers/{}_eruptions.tsv.gz"
EXCLUDE = {"Old_Faithful", "Daisy", "Riverside", "Grand", "Castle", "Beehive"}
SEL = RAW / "geyser_selection.json"


def geyser_intervals(data: bytes):
    import pandas as pd

    d = pd.read_csv(io.BytesIO(gzip.decompress(data)), sep="\t", low_memory=False)
    d = d[(d["associated_primaryID"] == d["eruptionID"]) & (d["A"] == 0) & (d["q"] == 0) & (d["eruption_time_epoch"] > 0)]
    t = np.sort(d["eruption_time_epoch"].to_numpy(float))
    iv = np.diff(t) / 60.0
    iv = iv[iv > 0]
    if len(iv) == 0:
        return iv, len(t), 0.0, 0
    gap = GAP_FACTOR * np.median(iv)
    ok = iv <= gap
    return iv[ok], len(t), float(gap), int((~ok).sum())


def prepare_geysers():
    if SEL.exists():
        return json.loads(SEL.read_text())
    page, err = fetch(GT_BASE, "archive_index.html")
    if page is None:
        sel = {"error": "archive listing fetch failed: " + err, "selected": []}
    else:
        names = sorted(set(re.findall(r"archive/geysers/([A-Za-z0-9_%.\-]+)_eruptions\.tsv\.gz", page.decode(errors="ignore"))))
        counts, failed = {}, {}
        for g in names:
            if g in EXCLUDE:
                continue
            data, e = fetch(GT_URL.format(g), f"geyser_{g}.tsv.gz")
            if data is None:
                failed[g] = e
                continue
            try:
                iv, *_ = geyser_intervals(data)
                counts[g] = int(len(iv))
            except Exception as ex:
                failed[g] = repr(ex)[:200]
        ranked = sorted(((c, g) for g, c in counts.items() if c >= 3000), key=lambda cg: (-cg[0], cg[1]))
        sel = {"listing_n": len(names), "counted": len(counts), "failed": failed, "n_ge_3000": len(ranked),
               "selected": [g for c, g in ranked[:12]], "counts": {g: c for c, g in ranked[:40]}}
    SEL.parent.mkdir(parents=True, exist_ok=True)
    SEL.write_text(json.dumps(sel, indent=1))
    return sel


def family_geysers():
    sel = json.loads(SEL.read_text()) if SEL.exists() else {"selected": [], "error": "run --prepare first"}
    if not sel["selected"]:
        yield "E:geyser/none", {"family": "E", "name": "geyser selection", "source": GT_BASE,
                                "reason": "pre-registered geyser selection rule", "status": "fetch failed",
                                "error": sel.get("error", "no geyser met the selection rule")}, None
        return
    for g in sel["selected"]:
        cid = f"E:geyser/{g}"
        meta = {"family": "E", "name": f"geyser {g}", "source": GT_URL.format(g),
                "reason": "interval alternation is a known geyser mechanism; tests how widely it holds (selected by the pre-registered rule: "
                          f"{sel['counts'].get(g)} valid intervals)"}
        data, err = fetch(GT_URL.format(g), f"geyser_{g}.tsv.gz")
        if data is None:
            yield cid, {**meta, "status": "fetch failed", "error": err}, None
            continue
        iv, n_ev, gap, dropped = geyser_intervals(data)
        ivk = iv[:CAP]
        x = threshold_stream(ivk)
        det = {"eruptions_kept": n_ev, "intervals_dropped_gap": dropped, "gap_threshold_min": round(gap, 1),
               "median_interval_min": round(float(np.median(ivk)), 1),
               "construction": "interval between consecutive eruptions (primary ID, A=0, q=0, no gap flag) > median of the used intervals; first 3000 in time order",
               "difference_of_series": False, "wn_r1_same_construction": wn_threshold(len(x))}
        yield finish(cid, meta, det, x)


# ---------------------------------------------------------------- E2: tennis serve
TENNIS_BASE = "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/"
TENNIS = [("men", "charting-m-points-to-2009.csv"), ("women", "charting-w-points-to-2009.csv")]


def family_tennis():
    import pandas as pd

    for tour, f in TENNIS:
        cid = f"E:tennis_first_server/{tour}"
        meta = {"family": "E", "name": f"tennis charting, first server wins the point ({tour})", "source": TENNIS_BASE + f,
                "reason": "the serve switches every game, so the first server's point-win probability switches regime each game"}
        data, err = fetch(TENNIS_BASE + f, f, timeout=600)
        if data is None:
            yield cid, {**meta, "status": "fetch failed", "error": err}, None
            continue
        d = pd.read_csv(io.BytesIO(data), usecols=["match_id", "Svr", "PtWinner"], low_memory=False)
        d = d.dropna(subset=["Svr", "PtWinner"])
        d = d[d["Svr"].isin([1, 2]) & d["PtWinner"].isin([1, 2])]
        first = d.groupby("match_id", sort=False)["Svr"].transform("first")
        x = (d["PtWinner"] == first).astype(int).to_numpy()[:CAP]
        det = {"matches_used": int(d["match_id"].iloc[:CAP].nunique()),
               "construction": "per point 1 if the winner is the match's first server; matches concatenated in file order; first 3000 points",
               "difference_of_series": False, "wn_r1_same_construction": wn_bernoulli(len(x), float(x.mean())) if len(x) > 2 else None}
        yield finish(cid, meta, det, x)


# ---------------------------------------------------------------- E3: collagens
COLLAGENS = [("P02452", "human COL1A1"), ("P08123", "human COL1A2"), ("P02461", "human COL3A1"),
             ("P02453", "bovine COL1A1"), ("P11087", "mouse Col1a1"), ("P08121", "mouse Col3a1")]


def family_collagen():
    for acc, nm in COLLAGENS:
        cid = f"E:collagen/{acc}"
        url = f"https://rest.uniprot.org/uniprotkb/{acc}.fasta"
        meta = {"family": "E", "name": f"collagen {nm} ({acc})", "source": url,
                "reason": "Gly-X-Y repeats impose periodicity on the sequence"}
        data, err = fetch(url, f"uniprot_{acc}.fasta", timeout=60)
        if data is None:
            yield cid, {**meta, "status": "fetch failed", "error": err}, None
            continue
        lines = data.decode().split("\n")
        s = "".join(l.strip() for l in lines if not l.startswith(">"))[:CAP]
        x = np.array([1 if c in p5.HYDRO else 0 for c in s])
        det = {"header": lines[0][:120], "length_used": len(s), "construction": "hydrophobic (IVLFCMA) indicator per residue, first 3000 residues",
               "difference_of_series": False, "wn_r1_same_construction": wn_bernoulli(len(x), float(x.mean())) if len(x) > 2 else None}
        yield finish(cid, meta, det, x)


# ---------------------------------------------------------------- E4: languages
GUTENDEX = "https://gutendex.com/books/"
LANGS = [("eu", "Basque"), ("af", "Afrikaans"), ("gl", "Galician"), ("oc", "Occitan"), ("fy", "Frisian"), ("br", "Breton"),
         ("ia", "Interlingua"), ("gd", "Scottish Gaelic"), ("lt", "Lithuanian"), ("lv", "Latvian"), ("et", "Estonian"),
         ("sk", "Slovak"), ("sl", "Slovenian"), ("hr", "Croatian"), ("sq", "Albanian")]
LATIN_BASE = set("aeiouy" + "àáâãäåæèéêëìíîïòóôõöøùúûüýÿœ")
EXTRA_VOWELS = set("āăąēĕėęěĩīĭįıōŏőũūŭůųű")


def resolve_book(code: str):
    err = "gutendex unreachable"
    for attempt in range(3):
        d = p5.curl(GUTENDEX, RAW / f"raw/gutendex_{code}.json", {"languages": code, "sort": "popular"}, timeout=60)
        time.sleep(1)
        if d:
            try:
                for b in json.loads(d)["results"]:
                    if any(k.startswith("text/plain") for k in b["formats"]):
                        return b["id"], b["title"], ""
                return None, None, "no plain-text book on first gutendex page"
            except (ValueError, KeyError) as e:
                return None, None, "bad gutendex response: " + repr(e)[:100]
        time.sleep(3)
    return None, None, err + " (3 attempts, curl timeout 60 s)"


def family_lang():
    for code, name in LANGS:
        cid = f"E:lang/{code}"
        meta = {"family": "E", "name": f"{name} ({code}) vowel/consonant", "source": GUTENDEX + f"?languages={code}&sort=popular",
                "reason": "alternation in phonotactics across language families; language not evaluated in Phases 4-6"}
        cache = RAW / f"raw/gutendex_{code}.json"
        if cache.exists() and cache.stat().st_size == 0:
            cache.unlink()
        bid, title, err = resolve_book(code)
        if not bid:
            yield cid, {**meta, "status": "fetch failed", "error": err}, None
            continue
        meta.update(book_id=bid, title=title)
        text, src = p5.fetch_book(int(bid))
        if text is None:
            yield cid, {**meta, "status": "fetch failed", "error": src}, None
            continue
        vowels = LATIN_BASE | EXTRA_VOWELS | ({"ë"} if code == "sq" else set())

        def ok(ch, vowels=vowels):
            return ch.isascii() or ch in vowels or (ch.isalpha() and ord(ch) < 0x0250)

        L = p5.p4b.letters(text, ok)
        if len(L) < 1000:
            yield cid, {**meta, "status": f"too few letters ({len(L)})", "error": "fetch failed: too few usable letters", "n": len(L)}, None
            continue
        xv = np.array([1 if ch in vowels else 0 for ch in L])
        det = {"source_text": src, "construction": "vowel indicator over letters 2000-5000 of the book body (Phase 4b)",
               "difference_of_series": False, "wn_r1_same_construction": wn_bernoulli(len(xv), float(xv.mean()))}
        yield cid, {**meta, **det, **summary(xv)}, [("vowel=1", xv), ("consonant=1", 1 - xv)]


# ---------------------------------------------------------------- E5: cricket
CRIC = "https://cricsheet.org/downloads/ipl_json.zip"


def family_cricket():
    cid = "E:cricket/ipl_runs_scored"
    meta = {"family": "E", "name": "IPL ball-by-ball (Cricsheet): a run was scored off the ball", "source": CRIC,
            "reason": "strike rotation: odd runs swap the batter, so scoring per ball may alternate (exploratory)"}
    data, err = fetch(CRIC, "ipl_json.zip", timeout=600)
    if data is None:
        yield cid, {**meta, "status": "fetch failed", "error": err}, None
        return
    xs, n_match = [], 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = sorted((n for n in z.namelist() if re.fullmatch(r"\d+\.json", n)), key=lambda n: int(n[:-5]))
        for nm in names:
            m = json.loads(z.read(nm))
            for inn in m.get("innings", []):
                if inn.get("super_over"):
                    continue
                for ov in inn.get("overs", []):
                    for dl in ov.get("deliveries", []):
                        xs.append(int(dl["runs"]["total"] > 0))
            n_match += 1
            if len(xs) >= CAP:
                break
    x = np.array(xs[:CAP])
    det = {"matches_used": n_match, "construction": "1 if runs.total > 0 on the delivery; regular innings only; matches in ascending id order; first 3000 deliveries",
           "difference_of_series": False, "wn_r1_same_construction": wn_bernoulli(len(x), float(x.mean())) if len(x) > 2 else None}
    yield finish(cid, meta, det, x)


def main():
    RES.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    if PREPARE:
        sel = prepare_geysers()
        print(json.dumps({k: v for k, v in sel.items() if k != "failed"}, indent=1), "failed:", len(sel.get("failed", {})))
        return
    n = k = 0
    if SHARD:
        k, n = map(int, SHARD.split("/"))
        p5.OUT = RES / f"attempts_phase10c_shard{k}.jsonl"
        p5.LOG = RES / f"phase10c_shard{k}.log"
    done = p5.done_ids()
    idx = -1
    for fam in (family_geysers, family_tennis, family_collagen, family_lang, family_cricket):
        for cid, meta, streams in fam():
            idx += 1
            if SHARD and idx % n != k:
                continue
            if SMOKE:
                print(cid, {a: b for a, b in meta.items() if a not in ("reason",)}, flush=True)
                continue
            if cid in done:
                continue
            rec = {"id": cid, **meta}
            if streams is None:
                rec.setdefault("status", "fetch failed")
                rec["positive"] = False
            else:
                p5.log("PRE", cid, "n", meta.get("n"), "mean", meta.get("mean"), "r1", meta.get("r1"), "wn_r1", meta.get("wn_r1_same_construction"))
                rec.update(p5.eval_streams(cid, streams))
            p5.emit(rec)
            p5.log("DONE", cid, rec.get("status"), "positive", rec.get("positive"))


if __name__ == "__main__":
    main()
