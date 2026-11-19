"""Phase 4b (PROTOCOL.md Addendum D): vowel/consonant streams from the Project Gutenberg mirror.

Usage: PYTHONPATH=src uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/run_phase4b.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import run_phase3 as p3  # noqa: E402

RAW = ROOT / "data/raw/real_chains/phase4b"
RES = ROOT / "docs/paper4_continuation/rbdp/real_data/results"
OUT = RES / "attempts_phase4b.jsonl"
MIRROR = "https://gutenberg.pglaf.org"
GAP_MIN, RHO_POS = 0.1, 1e-3


def mirror_urls(book_id: int) -> list[str]:
    s = str(book_id)
    d = "/".join(s[:-1]) if len(s) > 1 else "0"
    base = f"{MIRROR}/{d}/{s}"
    return [f"{base}/{s}-0.txt", f"{base}/{s}.txt", f"{base}/{s}-8.txt"]


def fetch(book_id: int) -> tuple[str | None, str]:
    RAW.mkdir(parents=True, exist_ok=True)
    dest = RAW / f"{book_id}.txt"
    for url in mirror_urls(book_id):
        r = subprocess.run(["curl", "-sS", "-f", "-m", "90", "-o", str(dest), url], capture_output=True)
        if r.returncode == 0 and dest.exists() and 1000 < dest.stat().st_size < 6_000_000:
            data = dest.read_bytes()
            with open(RAW / "SOURCE_manifest.jsonl", "a") as f:
                f.write(json.dumps({"book_id": book_id, "url": url, "bytes": len(data),
                                    "sha256": hashlib.sha256(data).hexdigest(),
                                    "retrieved": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            return data.decode("utf-8", errors="ignore"), url
    return None, "all mirror paths failed"


def letters(text: str, script_ok) -> list[str]:
    s, e = text.find("*** START"), text.find("*** END")
    if s >= 0:
        text = text[text.find("\n", s) + 1 : e if e > s else None]
    return [c for c in text.lower() if c.isalpha() and script_ok(c)][2000:5000]


def evaluate(x: np.ndarray, tag: str) -> dict:
    e = p3.eval_stream(x, tag)
    cells = [c for c in e.get("cells_d1", []) if c.get("status") == "ok"]
    g1 = e["g1"]
    # Addendum D: structure = fitted model beats iid (held-out or BIC)
    iid_ok = bool(g1["bic_iid"] > min(g1["bic_hmm"], g1["bic_markov"]))  # structured model beats iid on BIC
    good = [c for c in cells if c["rho_Gamma"] > RHO_POS and c["C0"] - c["U_iid"] >= GAP_MIN]
    best = max(good, key=lambda c: c["rho_Gamma"]) if good else None
    return {"tag": tag, "n": int(len(x)), "r1": float(np.corrcoef(x[:-1], x[1:])[0, 1]), "mean": float(x.mean()),
            "fit": {k: e["fit"][k] for k in ("t01", "t10", "e0", "e1")}, "g1_raw": g1, "g1_iid_ok": iid_ok,
            "g2": e["g2"]["pass_"], "solver_params": e.get("solver_params"),
            "best_good_cell": None if best is None else {k: best[k] for k in ("T", "B", "rho_Gamma", "C0", "U_iid",
                                                                              "risk_causal_of_iid_policy")},
            "positive": bool(iid_ok and e["g2"]["pass_"] and best is not None),
            "cells": [{k: c[k] for k in ("T", "B", "rho_Gamma", "C0", "U_iid", "risk_causal_of_iid_policy")} for c in cells]}


def main() -> None:
    cands = json.load(open(RES / "phase4_candidates.json"))["items"]
    texts = [dict(id="T:" + c["key"], lang=c["key"], book_id=(c.get("resolved") or {}).get("book_id"), vowels=c["vowels"])
             for c in cands if c["family"] == "T"]
    print(len(texts), "text candidates", flush=True)
    done = {json.loads(line)["id"] for line in open(OUT)} if OUT.exists() else set()
    n_pos = sum(json.loads(line).get("positive", False) for line in open(OUT)) if OUT.exists() else 0
    for c in texts:
        cid = c["id"]
        if cid in done or n_pos >= 10:
            continue
        rec = {"id": cid, "lang": c["lang"], "book_id": c["book_id"]}
        if not rec["book_id"]:
            rec.update(status="no book"); open(OUT, "a").write(json.dumps(rec) + "\n"); continue  # noqa: E702
        text, src = fetch(int(rec["book_id"]))
        rec["source"] = src
        if text is None:
            rec.update(status="fetch failed"); open(OUT, "a").write(json.dumps(rec) + "\n"); continue  # noqa: E702
        vowels = set(c["vowels"])
        lang = rec["lang"]
        if lang == "ru":
            def ok(ch):
                return "Ѐ" <= ch <= "ӿ"
        elif lang == "el":
            def ok(ch):
                return "Ͱ" <= ch <= "Ͽ" or "ἀ" <= ch <= "῿"
        else:
            def ok(ch):
                return ch.isascii() or ch in vowels or ch.isalpha() and ord(ch) < 0x0250
        L = letters(text, ok)
        if len(L) < 1000:
            rec.update(status=f"too few letters ({len(L)})"); open(OUT, "a").write(json.dumps(rec) + "\n"); continue  # noqa: E702
        xv = np.array([1 if ch in vowels else 0 for ch in L])
        rec["status"] = "evaluated"
        rec["streams"] = []
        for orient, x in (("vowel=1", xv), ("consonant=1", 1 - xv)):
            r = evaluate(x, f"{cid}_{orient}")
            r["orientation"] = orient
            if r["positive"]:  # shuffle control
                rng = np.random.default_rng(20261117)
                sh = []
                for k in range(5):
                    xs = rng.permutation(x)
                    rs = evaluate(xs, f"{cid}_{orient}_shuf{k}")
                    sh.append({"positive": rs["positive"], "g1_iid_ok": rs["g1_iid_ok"], "r1": rs["r1"]})
                r["shuffles"] = sh
                r["positive"] = sum(s["positive"] for s in sh) <= 1
            rec["streams"].append(r)
            print(cid, lang, orient, "r1 %.3f" % r["r1"], "pos", r["positive"], r["best_good_cell"], flush=True)
        rec["positive"] = any(s["positive"] for s in rec["streams"])
        n_pos += rec["positive"]
        open(OUT, "a").write(json.dumps(rec) + "\n")
        print("TALLY positive", n_pos, flush=True)


if __name__ == "__main__":
    main()
