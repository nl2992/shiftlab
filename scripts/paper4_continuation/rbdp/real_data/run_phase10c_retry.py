"""Phase 10c retry of the 13 gutendex-failed languages (PHASE10_PROTOCOL.md, "Phase 10c retry")."""
from __future__ import annotations

import csv
import io
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase10c as m  # noqa: E402

p5, RES, RAW = m.p5, m.RES, m.RAW
p5.OUT = RES / "attempts_phase10c_retry.jsonl"
p5.LOG = RES / "phase10c_retry.log"
CODES = "eu fy lt sl lv hr gl ia et sq oc gd sk".split()
NAMES = dict(m.LANGS)
CAT = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"


def catalog():
    d, err = m.fetch(CAT, "pg_catalog.csv", timeout=300, retries=2)
    if d is None:
        return None, err
    return list(csv.DictReader(io.StringIO(d.decode("utf-8", errors="ignore")))), ""


def stream_from_text(text, code):
    vowels = m.LATIN_BASE | m.EXTRA_VOWELS | ({"ë"} if code == "sq" else set())
    ok = lambda ch: ch.isascii() or ch in vowels or (ch.isalpha() and ord(ch) < 0x0250)  # noqa: E731
    s, e = text.find("*** START"), text.find("*** END")
    body = text[text.find("\n", s) + 1: e if e > s else None] if s >= 0 else text
    L = [c for c in body.lower() if c.isalpha() and ok(c)]
    if len(L) < 3000:
        return None, len(L), None
    if len(L) >= 5000:
        L, win = L[2000:5000], "letters 2000-5000"
    else:
        L, win = L[:3000], "first 3000 letters (body < 5000 letters)"
    return np.array([1 if c in vowels else 0 for c in L]), len(L), win


def main():
    done = p5.done_ids()
    cat, cerr = None, ""
    cat_tried = False
    for code in CODES:
        cid = f"E:lang/{code}"
        if cid in done:
            continue
        name = NAMES[code]
        meta = {"family": "E", "name": f"{name} ({code}) vowel/consonant", "retry_of": cid,
                "reason": "alternation in phonotactics across language families; language not evaluated in Phases 4-6; retry of a gutendex fetch failure"}
        bid, title, err = m.resolve_book(code)
        method = "gutendex (original rule)"
        text = src = None
        if bid:
            text, src = p5.fetch_book(int(bid))
            if text is None:
                err = "mirror: " + str(src)
            else:
                meta.update(source={"ebook_id": int(bid), "url": src}, title=title)
        if text is None:
            method = "pg_catalog fallback (lowest-numbered Text ebook with >= 3000 letters)"
            meta["gutendex_error"] = err
            if not cat_tried:
                cat, cerr = catalog()
                cat_tried = True
            if cat is None:
                p5.emit({"id": cid + "/retry", **meta, "status": "fetch failed", "error": "catalog: " + cerr, "positive": False})
                continue
            cands = sorted((int(r["Text#"]) for r in cat if r.get("Type") == "Text"
                            and code in [l.strip() for l in r.get("Language", "").split(";")]))
            meta["catalog_candidates"] = len(cands)
            x = None
            for bid in cands:
                text, src = p5.fetch_book(bid)
                if text is None:
                    continue
                x, nl, win = stream_from_text(text, code)
                if x is not None:
                    meta.update(source={"ebook_id": bid, "url": src}, window=win)
                    break
            if x is None:
                p5.emit({"id": cid + "/retry", **meta, "status": "fetch failed", "error": f"no catalog ebook met the rule ({len(cands)} candidates)", "positive": False})
                continue
        else:
            x, nl, win = stream_from_text(text, code)
            if x is None:
                p5.emit({"id": cid + "/retry", **meta, "status": f"too few letters ({nl})", "positive": False})
                continue
            meta["window"] = win
        det = {"selection_method": method, "construction": "vowel indicator (Phase 4b/Phase 10c af, br construction)",
               "difference_of_series": False, "wn_r1_same_construction": m.wn_bernoulli(len(x), float(x.mean()))}
        s = m.summary(x)
        p5.log("PRE", cid, "n", s["n"], "mean", s["mean"], "r1", s["r1"], "wn_r1", det["wn_r1_same_construction"], method)
        rec = {"id": cid + "/retry", **meta, **det, **s}
        rec.update(p5.eval_streams(cid, [("vowel=1", x), ("consonant=1", 1 - x)]))
        p5.emit(rec)
        p5.log("DONE", cid, rec.get("status"), "positive", rec.get("positive"))


if __name__ == "__main__":
    main()
