"""Phase 6 (PROTOCOL.md Addendum F): S2 silk, S3 elastin orthologues, L2 more languages, until the total is 25.

Usage: PYTHONPATH=src uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/run_phase6.py [--smoke]
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase5 as p5  # noqa: E402  (reused helpers; module globals redirected below)

ROOT = p5.ROOT
RES = p5.RES
p5.RAW = ROOT / "data/raw/real_chains/phase6"
p5.OUT = RES / "attempts_phase6.jsonl"
p5.LOG = RES / "phase6_run.log"
p5.MANIFEST = p5.RAW / "SOURCE_manifest.jsonl"
p5.START = 20
TARGET = 25
SMOKE = "--smoke" in sys.argv
RAW, OUT = p5.RAW, p5.OUT
GUTENDEX = "https://gutendex.com/books/"
EXCLUDE = {"P15502", "P04985", "Q99372", "P54320"}
LATIN_BASE = set("aeiouy" + "àáâãäåæèéêëìíîïòóôõöøùúûüýÿœ")
LANGS2 = [("cy", "Welsh"), ("is", "Icelandic"), ("no", "Norwegian"), ("tl", "Tagalog"), ("ga", "Irish"),
          ("sw", "Swahili"), ("id", "Indonesian")]


def uniprot_entries(query: str, fname: str, limit: int | None, dedupe: bool):
    data = None
    for _ in range(3):
        data = p5.curl(p5.UNIPROT, RAW / fname, {"query": query, "format": "fasta", "size": "100"}, timeout=90)
        if data:
            break
        time.sleep(2)
    if data is None:
        return None
    seen, out = set(), []
    for blk in data.decode().split(">")[1:]:
        head, *seq = blk.split("\n")
        m = re.match(r"(\S+)\s+(.*?)\s+OS=(.*?)\s+OX=", head)
        if not m:
            continue
        acc, name, org = m.group(1).split("|")[1], m.group(2), m.group(3)
        if acc in EXCLUDE:
            continue
        if dedupe:
            if (name, org) in seen:
                continue
            seen.add((name, org))
        out.append((acc, name, org, "".join(seq)))
        if limit and len(out) == limit:
            break
    return out


def protein_family(tag, fam, query, fname, limit, dedupe):
    ents = uniprot_entries(query, fname, limit, dedupe)
    if ents is None:
        yield f"{tag}:fetch", {"family": fam, "status": "fetch failed", "source": query}, None
        return
    for acc, name, org, s in ents:
        s = s[:3000]
        x = np.array([1 if c in p5.HYDRO else 0 for c in s])
        yield f"{tag}:{acc}", {"family": fam, "name": name, "organism": org, "length_used": len(s)}, p5.both(x)


def family_S2():
    q = "(protein_name:fibroin OR protein_name:spidroin) AND reviewed:true AND length:[300 TO *]"
    yield from protein_family("S2", "S2", q, "uniprot_s2.fasta", 8, True)


def family_S3():
    yield from protein_family("S3", "S3", "gene_exact:ELN AND reviewed:true", "uniprot_s3_eln.fasta", None, False)


def resolve_book(code: str):
    """Most-downloaded plain-text book on Gutendex for a language code (first page, popular order)."""
    for attempt in range(3):
        d = p5.curl(GUTENDEX, RAW / f"gutendex_{code}.json", {"languages": code, "sort": "popular"}, timeout=60)
        time.sleep(1)
        if d:
            try:
                for b in json.loads(d)["results"]:
                    if any(k.startswith("text/plain") for k in b["formats"]):
                        return b["id"], b["title"]
            except (ValueError, KeyError):
                pass
            return None, None
        time.sleep(3)
    return None, "gutendex unreachable"


def family_L2():
    cands = {c["key"]: c for c in json.load(open(RES / "phase4_candidates.json"))["items"] if c["family"] == "T"}
    jobs = [("eo", "Esperanto", (cands["eo"].get("resolved") or {}).get("book_id"), None)]
    for code, name in LANGS2:
        jobs.append((code, name, None, "resolve"))
    for code, name, bid, mode in jobs:
        base = {"family": "L2", "lang": code, "language": name}
        if mode == "resolve":
            bid, title = resolve_book(code)
            base["title"] = title
        base["book_id"] = bid
        if not bid:
            yield f"L2:{code}", {**base, "status": "fetch failed", "note": "no book resolved"}, None
            continue
        text, src = p5.fetch_book(int(bid))
        base["source"] = src
        if text is None:
            yield f"L2:{code}", {**base, "status": "fetch failed"}, None
            continue
        vowels = LATIN_BASE | ({"w", "ŵ", "ŷ"} if code == "cy" else set())
        if code == "eo":
            vowels = set(cands["eo"]["vowels"])

        def ok(ch, vowels=vowels):
            return ch.isascii() or ch in vowels or ch.isalpha() and ord(ch) < 0x0250

        L = p5.p4b.letters(text, ok)
        if len(L) < 1000:
            yield f"L2:{code}", {**base, "status": f"too few letters ({len(L)})"}, None
            continue
        xv = np.array([1 if ch in vowels else 0 for ch in L])
        yield f"L2:{code}", base, [("vowel=1", xv), ("consonant=1", 1 - xv)]


def main():
    RES.mkdir(parents=True, exist_ok=True)
    done = p5.done_ids()
    for fam in (family_S2, family_S3, family_L2):
        for cid, meta, streams in fam():
            if SMOKE:
                print(cid, meta, None if streams is None else [(o, len(x), int(np.sum(x)), round(float(np.corrcoef(x[:-1], x[1:])[0, 1]), 3)) for o, x in streams], flush=True)
                continue
            if cid in done:
                continue
            if p5.tally() >= TARGET:
                p5.log("TARGET reached; stopping")
                return
            rec = {"id": cid, **meta}
            if streams is None:
                rec.setdefault("status", "fetch failed")
                rec["positive"] = False
            else:
                rec.update(p5.eval_streams(cid, streams))
            p5.emit(rec)
            p5.log("DONE", cid, rec.get("status"), "positive", rec.get("positive"), "TALLY", p5.tally())
    p5.log("lists exhausted; final tally", p5.tally())


if __name__ == "__main__":
    main()
