"""B3+ experiment runner: resumable, paired, cache-based (no downloads, no model retraining).

Consumes the frozen-pair per-event losses cached by the B3 run
(``docs/promising_directions/results/b3/losses/{stream}.npz``: ``starts (K,)``, ``l0``/``l1``
``(K, 2000) int8``). Query-randomisation draws reproduce B3's ``episode_u`` (same SEED_BASE, same
``SeedSequence([seed_base, episode, seed])``) and are shared by every variant (paired design).

Output: ``{out}/{stream}__{config}__h{horizon}.jsonl`` (never touches ``results/b3``),
``provenance.json`` (list of runs) and ``SHA256SUMS.txt``.

Net cost per seed = loss + cq * queries + cs * switches, then averaged over seeds (as B3).
P1 is a HINDSIGHT reference (non-deployable). S5 needs cached alternative-pair losses.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import b3_plus_baselines as base

try:  # P7 variants arrive from a separately written module; never stubbed here.
    from b3_plus_policy import PlusParams, run_plus_policies

    PLUS_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on file presence
    PlusParams = run_plus_policies = None
    PLUS_AVAILABLE = False

ROOT = base.ROOT
b1 = base.b1
CACHE = ROOT / "docs/promising_directions/results/b3/losses"
DEFAULT_OUT = ROOT / "docs/promising_directions/results/b3_plus"
SEED_BASE = 20261101
T_FULL = 2000
BASE_VARIANTS = ("P0", "P1", "P2", "P3b", "P6", "PCT")


def _plus_params(v):
    """P7s/P7sp use the settled-decision acquisition shape (Phase 1c)."""
    if v in ("P7s", "P7sp"):
        return PlusParams(
            variant=v, acq_shape="settled", r_max=1.0, r_floor=0.25, settled_floor=0.0
        )
    return PlusParams(variant=v)


PLUS_VARIANTS = ("P4ref", "P7a", "P7b", "P7", "P7c", "P7s", "P7sp")
ALL_VARIANTS = (
    "P0",
    "P1",
    "P2",
    "P3b",
    "P6",
    "PCT",
    "P4ref",
    "P7a",
    "P7b",
    "P7",
    "P7c",
    "P7s",
    "P7sp",
)
STREAMS_ALL = ("spam", "rialto", "weather", "airlines", "bank", "elec2", "criteo")
# Phase 3.1 table: budget at T=2000, cs, cq, delay multiplier (None = protocol delay), alt pair.
CONFIGS = {
    "S0": {"budget": 200, "cs": 5.0, "cq": 0.05, "delay_mult": 1, "alt": False},
    "S1": {"budget": 400, "cs": 5.0, "cq": 0.05, "delay_mult": 1, "alt": False},
    "S2": {"budget": 200, "cs": 20.0, "cq": 0.05, "delay_mult": 1, "alt": False},
    "S3": {"budget": 200, "cs": 5.0, "cq": 0.05, "delay_mult": 2, "alt": False},
    "S4": {"budget": 200, "cs": 5.0, "cq": 0.10, "delay_mult": 1, "alt": False},
    "S5": {"budget": 200, "cs": 5.0, "cq": 0.05, "delay_mult": 1, "alt": True},
}


# ----------------------------------------------------------------------------- helpers
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False)
    return r.stdout.strip()


def variant_set_hash(variants) -> str:
    """Resume key over the variant set AND the plus-parameters each name resolves to.

    Hashing names alone is not enough: re-running a variant after a parameter change (e.g. P7s
    with a different settled_floor) then collides on the names but not the behaviour, leaving two
    entries per episode under one name and making assembled tables depend on merge order. This
    bit the S0/S2/S4 files once and the S1/S3 files a second time, so the parameters are folded
    into the key. Variants with no plus-parameters contribute their name only.
    """
    parts = []
    for v in sorted(variants):
        parts.append(v)
        if PlusParams is not None and v in PLUS_VARIANTS and v != "P4ref":
            p = _plus_params(v)
            parts.append(repr(dataclasses.astuple(p)) if dataclasses.is_dataclass(p) else repr(p))
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def episode_u(ep_index: int, n_seeds: int, t_len: int, seed_base: int = SEED_BASE) -> np.ndarray:
    """(T, n_seeds) draws. For t_len == 2000 this is b3_real_data.episode_u (same seeding)."""
    cols = [
        np.random.default_rng(np.random.SeedSequence([seed_base, ep_index, j])).random(t_len)
        for j in range(n_seeds)
    ]
    return np.stack(cols, axis=1)


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def append_rows(path: Path, rows: list[dict]) -> None:
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(b1.jsonable(r)) + "\n")


def row_key(r: dict) -> tuple:
    return (r["stream"], r["episode"], r["config"], r["horizon"], r["variant_set_hash"])


# ----------------------------------------------------------------------------- data
def load_stream(data_root: Path, stream: str, alt: bool):
    """Return (starts, l0, l1, base_err, files_read). Exits with a clear message if unavailable."""
    path = data_root / "alt" / f"{stream}.npz" if alt else data_root / f"{stream}.npz"
    if not path.exists():
        if alt:
            raise SystemExit(
                f"S5 (alternative model pair) cannot run: no cached alternative-pair losses at {path}. "
                "Producing them needs the raw data root (the B3 RAW path is on another machine) "
                "and model retraining; this runner does not synthesise an alternative pair."
            )
        raise SystemExit(f"cached losses not found for stream '{stream}': {path}")
    z = np.load(path)
    files = [path]
    if alt:
        if "base_err" not in z.files:
            raise SystemExit(
                f"S5 file {path} lacks a 'base_err' array (dev-window incumbent error)"
            )
        base_err = float(z["base_err"])
    else:
        pc = data_root.parent / "pairs_check.json"
        if not pc.exists():
            raise SystemExit(
                f"need {pc} (dev-window incumbent error recorded by B3) for P2's nominal"
            )
        base_err = float(json.loads(pc.read_text())[stream]["run"]["audit"]["inc_err"])
        files.append(pc)
    return z["starts"], z["l0"], z["l1"], base_err, files


def slices(starts, l0, l1, horizon: int):
    """Yield (episode_id, parent_episode, start, l0_slice, l1_slice)."""
    k_ep = l0.shape[0]
    if horizon == T_FULL:
        for i in range(k_ep):
            yield i, i, int(starts[i]), l0[i], l1[i]
    else:
        parts = T_FULL // horizon
        for i in range(k_ep):
            for h in range(parts):
                a = h * horizon
                yield (
                    i * parts + h,
                    i,
                    int(starts[i]) + a,
                    l0[i, a : a + horizon],
                    l1[i, a : a + horizon],
                )


# ----------------------------------------------------------------------------- one episode
def run_variants(l0, l1, u, budget, cs, cq, p, variants) -> dict:
    out = {}
    base_names = [v for v in variants if v in BASE_VARIANTS]
    plus_names = [v for v in variants if v in PLUS_VARIANTS]
    if base_names:
        out.update(base.run_baselines(l0, l1, u, budget, cs, cq, p, base_names))
    if plus_names:
        a0 = np.repeat(np.asarray(l0, dtype=np.int8)[:, None], u.shape[1], axis=1)
        a1 = np.repeat(np.asarray(l1, dtype=np.int8)[:, None], u.shape[1], axis=1)
        res = run_plus_policies(a0, a1, u, budget, cs, cq, p, [_plus_params(v) for v in plus_names])
        missing = [v for v in plus_names if v not in res]
        if missing:
            raise SystemExit(f"b3_plus_policy.run_plus_policies returned no result for {missing}")
        out.update({v: res[v] for v in plus_names})
    return out


def summarise_variant(d: dict, cq: float, cs: float) -> dict:
    cost = d["loss"] + cq * d["queries"] + cs * d["switches"]
    tp = np.asarray(d["t_prom"], dtype=float)
    promoted = ~np.isnan(tp)
    return {
        "mean_cost": float(cost.mean()),
        "mean_loss": float(np.mean(d["loss"])),
        "mean_labels": float(np.mean(d["queries"])),
        "mean_switches": float(np.mean(d["switches"])),
        "mean_rollbacks": float(np.mean(d["rollbacks"])),
        "promotion_rate": float(promoted.mean()),
        "mean_promotion_time": float(tp[promoted].mean()) if promoted.any() else None,
        "cost_seeds": [round(float(x), 6) for x in cost],
    }


# ----------------------------------------------------------------------------- provenance
def package_versions() -> dict:
    out = {}
    for pkg in ("numpy", "scipy", "pandas", "scikit-learn"):
        try:
            out[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            out[pkg] = None
    return out


def write_provenance(out: Path, args, files_read: set, seed_base: int) -> None:
    path = out / "provenance.json"
    cur = json.loads(path.read_text()) if path.exists() else {"runs": []}
    policy = HERE / "b3_plus_policy.py"
    status = git("status", "--porcelain")
    cur["runs"].append(
        {
            "git_head": git("rev-parse", "HEAD"),
            "git_dirty": bool(status),
            "losses_files_sha256": {str(f): sha256_file(f) for f in sorted(files_read)},
            "b3_plus_policy_sha256": sha256_file(policy) if policy.exists() else None,
            "b3_plus_baselines_sha256": sha256_file(HERE / "b3_plus_baselines.py"),
            "b3_plus_experiments_sha256": sha256_file(Path(__file__)),
            "b1_pinned_commit": base.B1_COMMIT,
            "b1_record": base.B1_RECORD,
            "python": sys.version,
            "platform": platform.platform(),
            "packages": package_versions(),
            "argv": sys.argv,
            "seed_base": seed_base,
            "n_seeds": args.n_seeds,
            "p1_note": "P1 is a hindsight reference, not a deployable policy",
            "utc": datetime.now(UTC).isoformat(),
        }
    )
    path.write_text(json.dumps(b1.jsonable(cur), indent=2), encoding="utf-8")


def write_sha256sums(out: Path) -> None:
    lines = [f"{sha256_file(p)} *{p.name}" for p in sorted(out.glob("*.jsonl"))]
    (out / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- main
def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--data-root",
        type=Path,
        default=CACHE,
        help="dir of cached {stream}.npz losses (alt pairs in alt/)",
    )
    ap.add_argument(
        "--streams", default="spam,rialto,weather", help=f"comma list from {','.join(STREAMS_ALL)}"
    )
    ap.add_argument(
        "--variants",
        default=",".join(ALL_VARIANTS),
        help=f"comma list; known: {','.join(BASE_VARIANTS + PLUS_VARIANTS)}",
    )
    ap.add_argument(
        "--config", action="append", choices=sorted(CONFIGS), help="repeatable; default S0"
    )
    ap.add_argument("--horizon", type=int, choices=(2000, 1000), default=2000)
    ap.add_argument("--n-seeds", type=int, default=100)
    ap.add_argument(
        "--max-episodes",
        type=int,
        default=None,
        help="debug/test: only the first N episodes per stream",
    )
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--resume", action="store_true", help="skip rows already present in the JSONL")
    ap.add_argument("--seed-base", type=int, default=SEED_BASE)
    return ap.parse_args(argv)


def main(argv=None) -> None:
    a = parse_args(argv)
    streams = [s for s in a.streams.split(",") if s]
    variants = [v for v in a.variants.split(",") if v]
    bad = [s for s in streams if s not in STREAMS_ALL]
    if bad:
        raise SystemExit(f"unknown stream(s) {bad}; allowed: {STREAMS_ALL}")
    bad = [v for v in variants if v not in BASE_VARIANTS + PLUS_VARIANTS]
    if bad:
        raise SystemExit(f"unknown variant(s) {bad}")
    plus_req = [v for v in variants if v in PLUS_VARIANTS]
    if plus_req and not PLUS_AVAILABLE:
        raise SystemExit(
            f"requested variant(s) {plus_req} need scripts/promising_directions/b3_plus_policy.py "
            "(PlusParams, run_plus_policies), which is not importable; refusing to skip or fake them."
        )
    configs = a.config or ["S0"]
    if any(CONFIGS[c]["alt"] for c in configs):  # fail early, before any work
        for s in streams:
            load_stream(a.data_root, s, alt=True)
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    vh = variant_set_hash(variants)
    files_read: set = set()
    t0 = time.time()
    for stream in streams:
        for cname in configs:
            cfg = CONFIGS[cname]
            starts, L0, L1, base_err, files = load_stream(a.data_root, stream, cfg["alt"])
            files_read.update(files)
            delay = base.STREAM_DELAYS[stream] * cfg["delay_mult"]
            budget = cfg["budget"] * a.horizon // T_FULL
            jsonl = out / f"{stream}__{cname}__h{a.horizon}.jsonl"
            done = (
                {
                    row_key(r)
                    for r in read_rows(jsonl)
                    if r["n_seeds"] == a.n_seeds and r["seed_base"] == a.seed_base
                }
                if a.resume
                else set()
            )
            if not a.resume and jsonl.exists():
                raise SystemExit(
                    f"{jsonl} exists; pass --resume to continue it or choose another --out"
                )
            p = b1.Params(T=a.horizon, delay=delay, base_err=base_err, eps=0.05)
            items = list(slices(starts, L0, L1, a.horizon))
            if a.max_episodes is not None:
                items = items[: a.max_episodes * (T_FULL // a.horizon)]
            for ep, parent, start, l0, l1 in items:
                key = (stream, ep, cname, a.horizon, vh)
                if key in done:
                    continue
                u = episode_u(ep, a.n_seeds, a.horizon, a.seed_base)
                res = run_variants(l0, l1, u, budget, cfg["cs"], cfg["cq"], p, variants)
                row = {
                    "stream": stream,
                    "episode": ep,
                    "parent_episode": parent,
                    "start": start,
                    "config": cname,
                    "horizon": a.horizon,
                    "budget": budget,
                    "cs": cfg["cs"],
                    "cq": cfg["cq"],
                    "delay": delay,
                    "n_seeds": a.n_seeds,
                    "seed_base": a.seed_base,
                    "variant_set_hash": vh,
                    "variant_meta": {
                        v: base.VARIANT_META.get(v, {"deployable": True}) for v in variants
                    },
                    "variants": {
                        v: summarise_variant(res[v], cfg["cq"], cfg["cs"]) for v in variants
                    },
                }
                append_rows(jsonl, [row])
                print(
                    f"[{stream} {cname} h{a.horizon}] episode {ep} {time.time() - t0:.0f}s",
                    flush=True,
                )
    write_provenance(out, a, files_read, a.seed_base)
    write_sha256sums(out)


if __name__ == "__main__":
    main()
