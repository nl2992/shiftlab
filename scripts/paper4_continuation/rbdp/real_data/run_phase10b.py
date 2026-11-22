"""Phase 10b (PHASE10_PROTOCOL.md, section "Phase 10b"): family D, dataset expansion by mechanism (alternation sources).
Same evaluator, shuffle control and positivity rule as Phases 5-10 (run_phase5.eval_streams); no stopping target; every
outcome (positive, null, fetch failed) is recorded with the reason the source was chosen.

Usage: PYTHONPATH=src python scripts/paper4_continuation/rbdp/real_data/run_phase10b.py [--smoke] [--shard=k/n]
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase5 as p5  # noqa: E402

ROOT, RES = p5.ROOT, p5.RES
p5.RAW = ROOT / "data/raw/real_chains/phase10b"
p5.OUT = RES / "attempts_phase10b.jsonl"
p5.LOG = RES / "phase10b_run.log"
p5.MANIFEST = p5.RAW / "SOURCE_manifest.jsonl"
RAW = p5.RAW
SMOKE = "--smoke" in sys.argv
SHARD = next((a.split("=")[1] for a in sys.argv if a.startswith("--shard=")), None)
CAP, MIN_N = 3000, 200
SEED = p5.SEED


def fetch(url: str, name: str, timeout: int = 300):
    """Returns (bytes | None, error string). Cached under RAW/raw/."""
    dest = RAW / "raw" / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest.read_bytes(), ""
    dest.parent.mkdir(parents=True, exist_ok=True)
    time.sleep(0.4)
    r = subprocess.run(["curl", "-sS", "-f", "-L", "-m", str(timeout), "-o", str(dest), url], capture_output=True)
    if r.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        if dest.exists():
            dest.unlink()
        return None, (r.stderr.decode(errors="ignore").strip() or f"curl exit {r.returncode}")[:300]
    data = dest.read_bytes()
    p5.manifest(url, data)
    return data, ""


def threshold_stream(v):
    """Level threshold: value above the median of the (capped) series. NOT a difference."""
    v = np.asarray(v, float)
    return (v > np.median(v)).astype(int)


def wn_check(n: int, seed: int = SEED):
    """White-noise control for the construction: same level-threshold applied to i.i.d. noise of the same length."""
    x = threshold_stream(np.random.default_rng(seed).standard_normal(n))
    return round(float(np.corrcoef(x[:-1], x[1:])[0, 1]), 3)


def summary(x):
    x = np.asarray(x, int)
    r1 = float(np.corrcoef(x[:-1], x[1:])[0, 1]) if x.std() > 0 else float("nan")
    return {"n": int(len(x)), "mean": round(float(x.mean()), 4), "r1": round(r1, 4)}


# ---------------------------------------------------------------- D1: geysers
GEYSERS = [
    ("Old_Faithful", "Old Faithful, recent independent record (eruptions from 2020-01-01); bimodal long/short intervals", 1577836800),
    ("Daisy", "Daisy: strongly bimodal short/long interval regimes", 0),
    ("Riverside", "Riverside: regular periodic geyser", 0),
    ("Grand", "Grand: periodic with series structure", 0),
    ("Castle", "Castle: periodic, major/minor eruption behaviour", 0),
    ("Beehive", "Beehive: periodic with irregular intervals", 0),
]
GT_URL = "https://geysertimes.org/archive/geysers/{}_eruptions.tsv.gz"
GAP_FACTOR = 3.0


def family_geysers():
    import pandas as pd

    for g, why, t0 in GEYSERS:
        cid = f"D:geyser/{g}"
        url = GT_URL.format(g)
        meta = {"family": "D", "name": f"geyser {g}", "source": url,
                "reason": "Old Faithful's long/short interval alternation (already supporting) is a known mechanism in other periodic geysers; " + why}
        data, err = fetch(url, f"geyser_{g}.tsv.gz")
        if data is None:
            yield cid, {**meta, "status": "fetch failed", "error": err}, None
            continue
        d = pd.read_csv(io.BytesIO(gzip.decompress(data)), sep="\t", low_memory=False)
        n_raw = len(d)
        d = d[(d["associated_primaryID"] == d["eruptionID"]) & (d["A"] == 0) & (d["q"] == 0) & (d["eruption_time_epoch"] > max(t0, 0))]
        t = np.sort(d["eruption_time_epoch"].to_numpy(float))
        iv = np.diff(t) / 60.0
        iv = iv[iv > 0]
        gap = GAP_FACTOR * np.median(iv)
        ok = iv <= gap  # an interval longer than 3x the median spans unobserved eruptions: dropped, not bridged
        ivk = iv[ok][:CAP]
        x = threshold_stream(ivk)
        det = {"rows_raw": int(n_raw), "rows_kept": int(len(t)), "intervals_dropped_gap": int((~ok).sum()), "gap_threshold_min": round(float(gap), 1),
               "median_interval_min": round(float(np.median(ivk)), 1) if len(ivk) else None,
               "construction": "interval between consecutive eruptions (primary ID, A=0, q=0, no gap flag) > median of the used intervals; first 3000 in time order",
               "difference_of_series": False, "wn_r1_same_construction": wn_check(len(x)) if len(x) > 2 else None, "since_epoch": t0}
        if len(x) < MIN_N:
            yield cid, {**meta, **det, "status": f"too short ({len(x)})", "n": int(len(x))}, None
        else:
            yield cid, {**meta, **det, **summary(x)}, p5.both(x)


# ---------------------------------------------------------------- D2: tennis point-by-point
TENNIS = [("atp", ["pbp_matches_atp_main_archive.csv", "pbp_matches_atp_main_current.csv"]),
          ("wta", ["pbp_matches_wta_main_archive.csv", "pbp_matches_wta_main_current.csv"])]
TENNIS_BASE = "https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/"


def family_tennis():
    for tour, files in TENNIS:
        cid = f"D:tennis/{tour}"
        meta = {"family": "D", "name": f"tennis point-by-point {tour.upper()}", "source": TENNIS_BASE + files[0],
                "reason": "serve alternates by game, so 'player 1 wins the point' switches regime every game"}
        errs = []
        for f in files:
            data, err = fetch(TENNIS_BASE + f, f)
            if data is None:
                errs.append(f"{f}: {err}")
        if errs:
            yield cid, {**meta, "status": "fetch failed", "error": " | ".join(errs)}, None
        else:  # not reached while the repository is unavailable (Phase 10b run: 404 on every file)
            yield cid, {**meta, "status": "fetch failed", "error": "files fetched but no parser was validated"}, None


# ---------------------------------------------------------------- D3: Bach chorales
def family_bach():
    cid = "D:bach_chorales"
    url = "https://archive.ics.uci.edu/static/public/25/bach+chorales.zip"
    meta = {"family": "D", "name": "Bach chorales (UCI id 25)", "source": url,
            "reason": "melodic register alternation in chorale melodies"}
    data, err = fetch(url, "bach_chorales_25.zip")
    if data is None:
        yield cid, {**meta, "status": "fetch failed", "error": err}, None
        return
    import zipfile

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            raw = z.read("chorales.lisp.Z")
        txt = _unlzw(raw).decode("latin-1")
    except Exception as e:
        yield cid, {**meta, "status": "fetch failed", "error": repr(e)[:200]}, None
        return
    starts = [m.start() for m in re.finditer(r"\(\d+ \(\(st ", txt)]
    streams, n_ch = [], 0
    for a, b in zip(starts, starts[1:] + [len(txt)]):
        p = np.array([int(v) for v in re.findall(r"\(pitch (\d+)\)", txt[a:b])], float)
        if len(p) < 2:
            continue
        streams.append(threshold_stream(p))  # above the chorale's own median
        n_ch += 1
        if sum(len(s) for s in streams) >= CAP:
            break
    x = np.concatenate(streams)[:CAP]
    det = {"chorales_used": n_ch, "construction": "MIDI pitch of each event > median pitch of its chorale; chorales concatenated in file order; first 3000 events",
           "difference_of_series": False, "wn_r1_same_construction": wn_check(len(x))}
    if len(x) < MIN_N:
        yield cid, {**meta, **det, "status": f"too short ({len(x)})", "n": int(len(x))}, None
    else:
        yield cid, {**meta, **det, **summary(x)}, p5.both(x)


def _unlzw(raw: bytes) -> bytes:
    r = subprocess.run(["gzip", "-dc"], input=raw, capture_output=True)  # gzip reads compress(1) .Z streams
    if not r.stdout:
        raise RuntimeError("cannot decompress .Z: " + r.stderr.decode(errors="ignore")[:100])
    return r.stdout


# ---------------------------------------------------------------- D4: heart RR intervals (Fantasia)
FANTASIA = "https://physionet.org/files/fantasia/1.0.0/"
SUBJECTS = ["f1y01", "f1y02", "f1y03", "f1o01", "f1o02", "f1o03"]


def read_mit_annotations(b: bytes):
    """Minimal MIT-format annotation reader: returns (sample_index, type_code) arrays."""
    pos, t, i = 0, 0, 0
    ts, ty = [], []
    n = len(b)
    while i + 2 <= n:
        w = b[i] | (b[i + 1] << 8)
        i += 2
        if w == 0:
            break
        code, delta = w >> 10, w & 0x3FF
        if code == 59:  # SKIP: 32-bit interval follows (high word first)
            hi = b[i] | (b[i + 1] << 8)
            lo = b[i + 2] | (b[i + 3] << 8)
            t += (hi << 16) | lo
            i += 4
            continue
        if code in (60, 61, 62):  # NUM, SUB, CHN: no time change
            continue
        t += delta
        if code == 63:  # AUX: delta is the byte length of the aux string (padded to even)
            i += delta + (delta & 1)
            continue
        ts.append(t)
        ty.append(code)
    return np.array(ts), np.array(ty)


def family_heart():
    for s in SUBJECTS:
        cid = f"D:heart/{s}"
        meta = {"family": "D", "name": f"Fantasia RR intervals {s}", "source": FANTASIA + s + ".ecg",
                "reason": "respiratory sinus arrhythmia makes RR intervals oscillate"}
        hea, e1 = fetch(FANTASIA + s + ".hea", s + ".hea")
        ecg, e2 = fetch(FANTASIA + s + ".ecg", s + ".ecg")
        if hea is None or ecg is None:
            yield cid, {**meta, "status": "fetch failed", "error": e1 or e2}, None
            continue
        fs = float(hea.decode().split("\n")[0].split()[2].split("/")[0])
        ts, ty = read_mit_annotations(ecg)
        beats = ts[(ty >= 1) & (ty <= 13)]
        rr = np.diff(beats) / fs
        ok = (rr > 0.3) & (rr < 2.0)  # physiological range; excludes dropouts/gaps (dropped, not bridged)
        rr_k = rr[ok][:CAP]
        x = threshold_stream(rr_k)
        det = {"fs": fs, "beats": int(len(beats)), "rr_dropped": int((~ok).sum()), "median_rr_s": round(float(np.median(rr_k)), 3) if len(rr_k) else None,
               "construction": "RR interval (s) between consecutive annotated beats > median RR of the used intervals; first 3000 intervals",
               "difference_of_series": False, "wn_r1_same_construction": wn_check(len(x)) if len(x) > 2 else None}
        if len(x) < MIN_N:
            yield cid, {**meta, **det, "status": f"too short ({len(x)})", "n": int(len(x))}, None
        else:
            yield cid, {**meta, **det, **summary(x)}, p5.both(x)


# ---------------------------------------------------------------- D5: DNA (already screened in Phase 4)
def family_dna():
    yield "D:dna_purine_pyrimidine", {"family": "D", "name": "NCBI genomes purine/pyrimidine", "source": "results/attempts_phase4.jsonl (family G)",
                                       "reason": "already evaluated in Phase 4: 16 NCBI genomes (family G), all 'screened out'; not repeated",
                                       "status": "already evaluated in Phase 4"}, None


def main():
    RES.mkdir(parents=True, exist_ok=True)
    if SHARD:
        k, n = map(int, SHARD.split("/"))
        p5.OUT = RES / f"attempts_phase10b_shard{k}.jsonl"
        p5.LOG = RES / f"phase10b_shard{k}.log"
    done = p5.done_ids()
    idx = -1
    for fam in (family_geysers, family_tennis, family_bach, family_heart, family_dna):
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
                rec.update(p5.eval_streams(cid, streams))
            p5.emit(rec)
            p5.log("DONE", cid, rec.get("status"), "positive", rec.get("positive"))


if __name__ == "__main__":
    main()
