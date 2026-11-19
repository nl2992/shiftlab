"""Phase 4 (Addendum C) resolution and fetching: Gutendex + Project Gutenberg text, NCBI efetch DNA.
Key-free, no e-mail, no cookies. NCBI <= 3 requests/s (sleep 0.4 s). Files > ~5 MB: only the first 1 MB is read (Range).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data/raw/real_chains/phase4"
MANIFEST = RAW / "SOURCE_manifest.jsonl"
HDR = {"User-Agent": "research-fetch/1.0"}
LANGS = "en fr de es it pt nl sv da fi hu pl cs la ru el ro ca eo tr".split()
ACCS = ["NC_001422.1", "NC_001416.1", "NC_001604.1", "NC_001417.2", "NC_001802.1", "NC_045512.2", "NC_001669.1",
        "NC_003977.2", "NC_012920.1", "NC_005089.1", "NC_001224.1", "NC_001879.2", "NC_000913.3", "NC_000964.3",
        "NC_001133.9", "NC_001477.1"]
LATIN_BASE = set("aeiouy" + "àáâãäåæèéêëìíîïòóôõöøùúûüœýÿ")
LATIN_EXTRA = {"hu": set("őű"), "tr": set("ı"), "ro": set("ă")}
CYR = set("аеёиоуыэюя")
GREEK = set("αεηιουω" + "άέήίόύώϊϋΐΰ")
NS = "script: Latin letters for Latin-script languages, Cyrillic for ru, Greek for el"


def script_of(lang):
    return "CYRILLIC" if lang == "ru" else "GREEK" if lang == "el" else "LATIN"


def vowels_of(lang):
    if lang == "ru":
        return CYR
    if lang == "el":
        return GREEK
    return LATIN_BASE | LATIN_EXTRA.get(lang, set())


def order():
    """T1, G1, T2, G2, ... then the remaining ones."""
    out = []
    for i in range(max(len(LANGS), len(ACCS))):
        if i < len(LANGS):
            out.append(("T", LANGS[i]))
        if i < len(ACCS):
            out.append(("G", ACCS[i]))
    return out


def log_manifest(url, content):
    RAW.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "a") as fh:
        fh.write(json.dumps(dict(url=url, retrieved_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 bytes=len(content), sha256=hashlib.sha256(content).hexdigest())) + "\n")


def resolve_text(lang):
    r = None
    err = None
    for _ in range(2):  # one retry of the same request on timeout
        try:
            r = requests.get("https://gutendex.com/books/", params={"languages": lang, "sort": "popular"}, timeout=120,
                             headers=HDR)
            break
        except requests.RequestException as ex:
            err = f"{type(ex).__name__}: {ex}"
            time.sleep(2)
    if r is None:
        return dict(ok=False, error=f"gutendex request failed twice: {err}")
    if r.status_code != 200:
        return dict(ok=False, error=f"gutendex HTTP {r.status_code}")
    for b in r.json().get("results", []):
        for fmt, url in b["formats"].items():
            if fmt.startswith("text/plain"):
                return dict(ok=True, book_id=b["id"], title=b["title"], download_count=b.get("download_count"),
                            format=fmt, url=url, languages=b["languages"])
    return dict(ok=False, error="no plain-text book on first Gutendex page")


def fetch_text(lang, res):
    url = res["url"]
    time.sleep(0.5)
    big = False
    try:
        h = requests.head(url, timeout=60, allow_redirects=True, headers=HDR)
        cl = int(h.headers.get("Content-Length", -1))
        big = cl > 5_000_000
    except (requests.RequestException, ValueError):
        pass
    hdr = dict(HDR)
    if big:
        hdr["Range"] = "bytes=0-999999"
    r = requests.get(url, timeout=120, headers=hdr)
    if r.status_code not in (200, 206):
        raise RuntimeError(f"HTTP {r.status_code} for {url}")
    content = r.content
    log_manifest(url, content)
    (RAW / f"T_{lang}.txt").write_bytes(content)
    txt = content.decode("utf-8", errors="replace")
    m = re.search(r"\*\*\* ?START[^\n]*\n", txt)
    if m:
        txt = txt[m.end():]
    m = re.search(r"\*\*\* ?END", txt)
    if m:
        txt = txt[:m.start()]
    txt = txt.replace("İ", "i").lower()
    sc = script_of(lang)
    letters = [c for c in txt if c.isalpha() and unicodedata.name(c, "").startswith(sc)]
    if len(letters) < 5000:
        raise RuntimeError(f"only {len(letters)} script letters")
    seg = letters[2000:5000]
    v = vowels_of(lang)
    x = [int(c in v) for c in seg]
    return x, dict(n_letters_total=len(letters), range_read=big, bytes=len(content), vowel_fraction=sum(x) / len(x),
                   sample="".join(seg[:60]))


def fetch_dna(acc):
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=" + acc +
           "&rettype=fasta&retmode=text&seq_start=1001&seq_stop=4000")
    time.sleep(0.4)
    r = requests.get(url, timeout=60, headers=HDR)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:100]!r}")
    log_manifest(url, r.content)
    (RAW / f"G_{acc}.fasta").write_bytes(r.content)
    lines = r.text.splitlines()
    seq = "".join(lines[1:]).upper()
    bases = [c for c in seq if c in "ACGT"]
    if len(bases) < 500:
        raise RuntimeError(f"only {len(bases)} ACGT bases: {r.text[:100]!r}")
    ry = [int(c in "AG") for c in bases]
    sw = [int(c in "GC") for c in bases]
    return dict(RY=ry, SW=sw), dict(header=lines[0], n_bases=len(bases), bytes=len(r.content), n_nonacgt=len(seq) - len(bases))
