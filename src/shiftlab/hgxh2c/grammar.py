"""Typed transfer grammar for the HG x H2c search (PROTOCOL section 6).

A Candidate = 6 slots (direction BC|CB) x (channel S|Q|R), each slot a tuple of <=2 operators in
registry order, plus a J combiner and base engines (B, C). The 64 basic structures are the on/off
masks of the 6 slots. All candidates sharing (base engines, combiner kind) differ only in parameter
tensors: ``compile_batch`` turns any list of them into ONE wide Monitor (masked, param-tensor hooks).

Direction BC: source B, target C (H2c family; guide track gB, gamma .995). CB: source C, target B (HG
family; guide gC, gamma .99). Hooks read only predictable state (``Ctx``: released log-wealth, discounted
released moments, base stakes, spent budget, free proxies); stakes are clipped to [0, cap/Bd] and queries
to [q_floor, 1] by the engine, so every factor 1 + lam*x >= 1 - cap.
"""

from __future__ import annotations

import bisect
import hashlib
import itertools
import json
import math
from dataclasses import dataclass, replace

import torch

_enum = enumerate  # builtin; the public ``enumerate`` below shadows it in this module

from shiftlab.hgxh2c.baselines import JointContextualONS, xu_query
from shiftlab.hgxh2c.engines import LOG_THR, Hooks, Monitor, TrackSpec

DIRS = ("BC", "CB")
CHANS = ("S", "Q", "R")
SLOTS = tuple((d, c) for d in DIRS for c in CHANS)
SRC, TGT = {"BC": "B", "CB": "C"}, {"BC": "C", "CB": "B"}
GUIDE = {"BC": ("gB", 0.995), "CB": ("gC", 0.99)}
# A3.1: the same-step product is invalid under dependence (THEORY_AUDIT F1); 'linear' = 1 + w lam_B x_B + (1-w) lam_C x_C
# (split cap, predictable stakes, supermartingale under the joint null). 'prod' only appears among logged rejects.
COMBS = (("bonf", 0.0), ("mix", 0.25), ("mix", 0.5), ("mix", 0.75), ("linear", 0.5))
RAW_COMBS = COMBS + (("prod", 0.0),)
BASES = ("kelly", "ons", "grapa")
PREDICTABLE_S = {
    "logW",
    "mean",
    "base",
    "kelly",
    "spent",
    "hi",
    "bd",
}  # A3.2: S and R read released labels / past state only
PREDICTABLE_Q = PREDICTABLE_S | {"h", "res"}  # only Q may read the current free proxy at issue time
READS = {"S": PREDICTABLE_S, "Q": PREDICTABLE_Q, "R": PREDICTABLE_S}
BIG = 1e9


@dataclass(frozen=True)
class Op:
    names: tuple
    raw: tuple  # raw grid (includes identity / degenerate points that canonicalise rejects)
    rng: dict  # typed range per parameter name
    reads: tuple = ("logW",)
    bad: object = None  # params -> reason or None


def _b(f):
    return f


OPS = {
    ("S", "ratio"): Op(
        ("a", "ref"),
        tuple((a, r) for a in (0.0, 0.5, 1.0) for r in (0, 1)),
        {"a": (0, 1), "ref": (0, 1)},
        ("base", "kelly", "bd", "hi"),
        lambda p: "identity" if p[0] == 0 else ("discounted_kelly" if p[1] == 1 else None),
    ),
    ("S", "shift"): Op(
        ("a",),
        ((0.0,), (0.1,), (0.3,)),
        {"a": (0, 1)},
        ("base", "hi"),
        lambda p: "identity" if p[0] == 0 else None,
    ),
    ("S", "gate"): Op(
        ("thr",),
        ((-1.0,), (0.0,), (0.02,)),
        {"thr": (-1, 1)},
        ("mean",),
        lambda p: "identity" if p[0] <= -1 else None,
    ),
    ("S", "temper"): Op(
        ("c0",),
        ((1.0,), (0.25,), (0.5,)),
        {"c0": (1e-3, 1)},
        ("logW", "hi"),
        lambda p: "identity" if p[0] >= 1 else None,
    ),
    ("Q", "boost"): Op(
        ("b",),
        ((0.0,), (1.0,), (3.0,)),
        {"b": (0, 8)},
        ("logW",),
        lambda p: "identity" if p[0] == 0 else None,
    ),
    ("Q", "straddle"): Op(
        ("m", "lo"),
        tuple((m, lo) for m in (1.0, 2.0, 4.0) for lo in (0.0, 1.0)),
        {"m": (1, 8), "lo": (-5, 5)},
        ("logW",),
        lambda p: "identity" if p[0] == 1 else None,
    ),
    ("Q", "ipw"): Op(
        ("e",),
        ((0.0,), (0.5,), (1.0,)),
        {"e": (0, 1)},
        ("res", "h"),
        lambda p: "identity" if p[0] == 0 else None,
    ),
    ("Q", "pace"): Op(
        ("e", "k"),
        tuple((e, k) for e in (0.5, 1.0) for k in (1.0, 2.0)),
        {"e": (0, 2), "k": (0, 4)},
        ("logW", "spent"),
    ),
    ("R", "restart"): Op(
        ("k",),
        ((BIG,), (1.0,), (2.0,)),
        {"k": (1e-3, BIG)},
        ("logW",),
        lambda p: "identity" if p[0] >= BIG else None,
    ),
    ("R", "soft"): Op(
        ("rho",),
        ((1.0,), (0.3,), (0.6,)),
        {"rho": (0, 1)},
        ("logW",),
        lambda p: "identity" if p[0] >= 1 else None,
    ),
    ("R", "gamma"): Op(("g",), ((0.97,), (0.9,)), {"g": (1e-3, 1)}, ("logW",)),
}
ORDER = {c: [o for (ch, o) in OPS if ch == c] for c in CHANS}
DEFAULT = {
    "ref": 0,
    "thr": 0.0,
    "c0": 1.0,
    "m": 1.0,
    "k": 1.0,
    "e": 1.0,
    "rho": 1.0,
    "g": 0.97,
    "a": 0.0,
    "b": 0.0,
    "lo": 0.0,
}


def op_reason(chan, op, p):
    f = OPS[(chan, op)].bad
    return f(p) if f else None


@dataclass(frozen=True)
class Candidate:
    slots: tuple = ((),) * 6  # per SLOTS entry: tuple of (op, params)
    comb: str = "bonf"
    w: float = 0.0
    base: tuple = ("kelly", "kelly")  # base engines of tracks (B, C)
    qfl: float | None = None  # query floor as a fraction of the base rate; None = automatic

    def slot(self, d, c):
        return self.slots[SLOTS.index((d, c))]

    @property
    def structure(self) -> int:
        return sum(1 << i for i, s in _enum(self.slots) if s)

    @property
    def n_ops(self) -> int:
        return sum(len(s) for s in self.slots)

    def to_dict(self):
        return {
            "slots": [[[o, list(p)] for o, p in s] for s in self.slots],
            "comb": self.comb,
            "w": self.w,
            "base": list(self.base),
            "qfl": self.qfl,
        }

    @staticmethod
    def from_dict(d):
        return Candidate(
            tuple(tuple((o, tuple(p)) for o, p in s) for s in d["slots"]),
            d["comb"],
            d["w"],
            tuple(d["base"]),
            d.get("qfl"),
        )

    @property
    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()[:16]

    def without(self, i):
        return replace(self, slots=self.slots[:i] + ((),) + self.slots[i + 1 :])

    @property
    def group(self):
        """Batch key: base engines, combiner kind, and the expensive features (guide tracks per direction, residual-variance
        bins per source track) so cheap candidates never pay for them. Everything else is a [K,1] parameter tensor."""
        ops = lambda i: {o for o, _ in self.slots[i]}
        guide = tuple(bool(ops(i) & {"ratio", "gate"}) for i in (0, 3))
        bins = tuple("ipw" in ops(i) for i in (1, 4))
        return (self.base, self.comb, guide, bins)


# --------------------------------------------------------------------------- option lists / space
def _options(chan, grid):
    names = ORDER[chan]
    singles = [((o, p),) for o in names for p in grid[o]]
    pairs = [
        ((o1, p1), (o2, p2))
        for o1, o2 in itertools.combinations(names, 2)
        for p1 in grid[o1]
        for p2 in grid[o2]
    ]
    return [()] + singles + pairs


RAW_GRID = {c: {o: list(OPS[(c, o)].raw) for o in ORDER[c]} for c in CHANS}
CAN_GRID = {
    c: {o: [p for p in RAW_GRID[c][o] if op_reason(c, o, p) is None] for o in ORDER[c]}
    for c in CHANS
}
RAW = {c: _options(c, RAW_GRID[c]) for c in CHANS}
CAN = {c: _options(c, CAN_GRID[c]) for c in CHANS}
CAN_R_ONS = [
    o for o in CAN["R"] if all(op != "gamma" for op, _ in o)
]  # gamma switch is the identity for ONS targets
STRUCTURES = tuple(range(64))
BLOCKS = [(bB, bC, cb, w) for bB in BASES for bC in BASES for cb, w in COMBS]  # 45


def _slot_opts(slot_i, tgt_base):
    c = SLOTS[slot_i][1]
    return (CAN_R_ONS if (c == "R" and tgt_base == "ons") else CAN[c])[1:]  # non-off options


def _active(s):
    return [i for i in range(6) if s >> i & 1]


def _block_size(s, blk):
    bB, bC = blk[0], blk[1]
    n = 1
    for i in _active(s):
        n *= len(_slot_opts(i, bC if SLOTS[i][0] == "BC" else bB))
    return n


def space_size():
    can = {s: sum(_block_size(s, b) for b in BLOCKS) for s in STRUCTURES}
    raw = len(RAW_COMBS) * 9 * math.prod(len(RAW[c]) for c in CHANS) ** 2
    return {
        "structures": 64,
        "canonical": sum(can.values()) - can[0],
        "canonical_by_structure": can,
        "raw": raw,
        "blocks": len(BLOCKS),
    }


def _decode(s, j):
    """j-th canonical candidate of structure s (j < structure size)."""
    cum, tot = [], 0
    for b in BLOCKS:
        tot += _block_size(s, b)
        cum.append(tot)
    bi = bisect.bisect_right(cum, j)
    r = j - (cum[bi - 1] if bi else 0)
    blk = BLOCKS[bi]
    slots = [()] * 6
    for i in _active(s):
        opts = _slot_opts(i, blk[1] if SLOTS[i][0] == "BC" else blk[0])
        r, k = divmod(r, len(opts))
        slots[i] = opts[k]
    return Candidate(tuple(slots), blk[2], blk[3], (blk[0], blk[1]))


def enumerate_space(max_n, start=0, seed=0):
    """Structure-stratified, deterministic walk of the canonical space: round-robin over the 63
    non-empty structures, a coprime-stride permutation inside each. Yields Candidates (canonicalised)."""
    sizes = {s: sum(_block_size(s, b) for b in BLOCKS) for s in STRUCTURES if s}
    a = 2654435761
    n = 0
    rnd = start
    while n < max_n and any(rnd < z for z in sizes.values()):
        for s, z in sizes.items():
            if rnd < z and n < max_n:
                j = (a * rnd + 7919 * seed + s) % z if math.gcd(a, z) == 1 else (rnd + seed) % z
                c, _why = canonicalise(_decode(s, j))
                if c is not None:
                    yield c
                    n += 1
        rnd += 1


enumerate = enumerate_space  # public name (module-level alias; internals use the builtin)


def sample_raw(n, seed=0):
    """Random raw candidates (including degenerate grid points) for rejection logging."""
    import random

    rng = random.Random(seed)
    out = []
    for _ in range(n):
        slots = tuple(rng.choice(RAW[c]) for _, c in SLOTS)
        cb, w = rng.choice(RAW_COMBS)
        out.append(Candidate(slots, cb, w, (rng.choice(BASES), rng.choice(BASES))))
    return out


# --------------------------------------------------------------------------- typing / canonical form
def typing(c: Candidate):
    """Return None if typed, else 'UNTYPED:<why>'. Only predictable quantities, clipped stakes, q floor > 0."""
    if (
        c.comb not in ("bonf", "mix", "linear")
        or any(b not in BASES for b in c.base)
        or len(c.slots) != 6
    ):
        return "UNTYPED:structure"
    if c.comb in ("mix", "linear") and c.w not in (0.25, 0.5, 0.75):
        return "UNTYPED:mixture weight must be fixed in {.25,.5,.75}"
    if c.qfl is not None and not (0 < c.qfl <= 1):
        return "UNTYPED:q floor must be in (0,1]"
    for (d, ch), s in zip(SLOTS, c.slots):
        if len(s) > 2:
            return "UNTYPED:depth"
        last = -1
        for op, p in s:
            if (ch, op) not in OPS:
                return f"UNTYPED:unknown operator {op}"
            o = OPS[(ch, op)]
            if not set(o.reads) <= READS[ch]:
                return f"UNTYPED:{op} reads non-predictable {sorted(set(o.reads) - READS[ch])} in channel {ch}"
            if len(p) != len(o.names) or any(
                not (o.rng[n][0] <= v <= o.rng[n][1]) for n, v in zip(o.names, p)
            ):
                return f"UNTYPED:{op} params out of typed range"
            if ORDER[ch].index(op) <= last:
                return "UNTYPED:operator order"
            last = ORDER[ch].index(op)
    return None


def canonicalise(c: Candidate):
    """-> (candidate, None) or (None, reason). Reasons: UNTYPED:<why> | EQUIVALENT_TO:<rule>."""
    if c.comb == "prod":
        return None, "INVALID:product_cross_term"
    why = typing(c)
    if why:
        return None, why
    if not any(c.slots):
        return None, "EQUIVALENT_TO:no_transfer"
    for (d, ch), s in zip(SLOTS, c.slots):
        for op, p in s:
            r = op_reason(ch, op, p)
            if r:
                return None, f"EQUIVALENT_TO:{r}"
            if op == "gamma" and c.base[0 if TGT[d] == "B" else 1] == "ons":
                return None, "EQUIVALENT_TO:identity"
    return c, None


def audit_equivalence(cands, tape, tol=1e-9):
    """Post-hoc numerical canonicalisation on audit seeds: max |dlogW| (over B and C paths) against joint
    contextual ONS and against the no-transfer base engines. -> {hash: reason or None}."""
    from shiftlab.hgxh2c.baselines import JointContextualONS

    ref = JointContextualONS().monitor().run(tape, keep_paths=True)
    out = {}
    for grp in _groups(cands):
        none = {c.hash: replace(c, slots=((),) * 6) for c in grp}
        res = compile_batch(grp).run(tape, keep_paths=True)
        res0 = compile_batch(list(none.values())).run(tape, keep_paths=True)
        for k, c in _enum(grp):
            d_ctx = max(float((res.logW[t][k] - ref.logW[t][0]).abs().max()) for t in "BC")
            d_nt = max(float((res.logW[t][k] - res0.logW[t][k]).abs().max()) for t in "BC")
            out[c.hash] = (
                "EQUIVALENT_TO:joint_contextual_ons"
                if d_ctx < tol
                else ("EQUIVALENT_TO:no_transfer" if d_nt < tol else None)
            )
    return out


def _groups(cands):
    g = {}
    for c in cands:
        g.setdefault(c.group, []).append(c)
    return list(g.values())


# --------------------------------------------------------------------------- compile
class _P:
    """[K,1] parameter tensor. ``init`` allocates it on the device before step 0 (Hooks.declare), so no host->device
    copy happens inside a CUDA-graph capture."""

    def __init__(self, vals):
        self.v, self.t = vals, None

    def init(self, dev):
        self.t = torch.tensor(self.v, dtype=torch.float64, device=dev).view(-1, 1)

    def __call__(self, ref=None):
        return self.t


def _params(cands, d, ch, op):
    """(enable tensor factory or None if unused, [param factories])."""
    ms = [dict(c.slot(d, ch)) for c in cands]
    if not any(op in m for m in ms):
        return None
    names = OPS[(ch, op)].names
    en = _P([1.0 if op in m else 0.0 for m in ms])
    return en, [
        _P([float(m[op][j]) if op in m else DEFAULT[n] for m in ms]) for j, n in _enum(names)
    ]


def compile_batch(cands, name="cand", ctx_replace=False, graph=False) -> Monitor:
    """One wide Monitor for candidates that share (base engines, combiner kind); parameters become [K,1] tensors.
    ctx_replace: S slots are dropped and replaced by joint contextual ONS stakes (mechanism control)."""
    cands = list(cands)
    assert len({c.group for c in cands}) == 1, (
        "compile_batch needs one batch group (Candidate.group)"
    )
    c0 = cands[0]
    if ctx_replace:
        cands = [
            replace(c, slots=tuple(() if SLOTS[i][1] == "S" else c.slots[i] for i in range(6)))
            for c in cands
        ]
    P = {(d, ch, op): _params(cands, d, ch, op) for d in DIRS for ch in CHANS for op in ORDER[ch]}
    P = {k: v for k, v in P.items() if v is not None}
    used = lambda d, *ops: any((d, ch, op) in P for ch, op in ops)
    tracks = []
    for d in DIRS:
        if used(d, ("S", "ratio"), ("S", "gate")):
            g, gg = GUIDE[d]
            tracks.append(TrackSpec(g, ch=SRC[d], gamma=gg, bet=False))
    gam = lambda b, ch: {"B": 0.99, "C": 0.995}[ch] if b == "kelly" else 1.0
    for ch, b in zip("BC", c0.base):
        bins = 8 if any((d, "Q", "ipw") in P for d in DIRS if SRC[d] == ch) else 0
        tracks.append(TrackSpec(ch, base=b, gamma=gam(b, ch), bins=bins))

    def stake(d):
        src, tgt, g = SRC[d], TGT[d], GUIDE[d][0]
        ops = {op: P[(d, "S", op)] for op in ORDER["S"] if (d, "S", op) in P}
        if not ops:
            return None

        def f(ctx, lam):
            hi = ctx.hi[tgt]
            if "ratio" in ops:
                en, (a, rf) = ops["ratio"]
                own = torch.minimum(ctx.kelly[tgt].clamp(min=0.0), hi)
                gd = (
                    torch.where(rf(hi) > 0, own, ctx.base[g] * ctx.bd[g] / ctx.bd[tgt])
                    if g in ctx.base
                    else own
                )
                lam = torch.where(en(hi) > 0, (1 - a(hi)) * lam + a(hi) * gd, lam)
            if "shift" in ops:
                en, (a,) = ops["shift"]
                lam = torch.where(en(hi) > 0, lam + a(hi) * hi * ctx.base[src] / ctx.hi[src], lam)
            if "gate" in ops:
                en, (thr,) = ops["gate"]
                lam = torch.where(en(hi) > 0, lam * (ctx.mean[g] > thr(hi)), lam)
            if "temper" in ops:
                en, (c0_,) = ops["temper"]
                fr = c0_(hi) + (1 - c0_(hi)) * (ctx.logW[src] / LOG_THR).clamp(0.0, 1.0)
                lam = torch.where(en(hi) > 0, torch.minimum(lam, hi * fr), lam)
            return lam

        return f

    def query(ctx, q):
        for d in DIRS:
            src = SRC[d]
            u = (ctx.logW[src] / LOG_THR).clamp(0.0, 1.0)
            if (d, "Q", "boost") in P:
                en, (b,) = P[(d, "Q", "boost")]
                q = torch.where(en(u) > 0, q * (1 + b(u) * u), q)
            if (d, "Q", "straddle") in P:
                en, (m, lo) = P[(d, "Q", "straddle")]
                q = torch.where(
                    (en(u) > 0) & (ctx.logW[src] >= lo(u)) & (ctx.logW[src] < LOG_THR), q * m(u), q
                )
            if (d, "Q", "ipw") in P:
                en, (e,) = P[(d, "Q", "ipw")]
                q = torch.where(en(u) > 0, q * xu_query(src)(ctx, torch.ones_like(q)) ** e(u), q)
            if (d, "Q", "pace") in P:
                en, (e, k) = P[(d, "Q", "pace")]
                ratio = ((ctx.budget - ctx.spent) / (ctx.T - ctx.tt).clamp(min=1)) / (
                    ctx.budget / ctx.T
                )
                q = torch.where(en(u) > 0, q * ratio.clamp(0.5, 2.0) ** e(u) * (0.5 + k(u) * u), q)
        return q

    prev = {}  # direction -> [K,S] previous source log-wealth, allocated in declare, updated in place

    def restart(d):
        src = SRC[d]
        if not (used(d, ("R", "restart"), ("R", "soft"))):
            return None

        def f(ctx):
            cur, pv = ctx.logW[src], prev[d]
            keep = torch.ones_like(cur)
            if (d, "R", "restart") in P:
                en, (k,) = P[(d, "R", "restart")]
                keep = torch.where(
                    (en() > 0) & (cur >= k()) & (pv < k()), torch.zeros_like(keep), keep
                )
            if (d, "R", "soft") in P:
                en, (rho,) = P[(d, "R", "soft")]
                keep = torch.where(
                    (en() > 0) & (cur >= 0.5) & (pv < 0.5),
                    torch.minimum(keep, rho().expand_as(keep)),
                    keep,
                )
            pv.copy_(cur)
            return keep

        return f

    def gamma(d):
        if (d, "R", "gamma") not in P:
            return None
        en, (g,) = P[(d, "R", "gamma")]
        return lambda ctx, gm: torch.where((en(gm) > 0) & (ctx.logW[SRC[d]] >= 1.0), g(gm), gm)

    hk = Hooks()
    for d in DIRS:
        for store, fn in ((hk.stake, stake(d)), (hk.restart, restart(d)), (hk.gamma, gamma(d))):
            if fn:
                store[TGT[d]] = fn
    if any(k[1] == "Q" for k in P):
        hk.query = query
    if ctx_replace:
        jc = JointContextualONS()
        hk.stake.update({n: jc.stake(n) for n in "BC"})
        hk.after_step = jc.after

    def declare(ctx):
        for en, ps in P.values():
            en.init(ctx.device)
            for p in ps:
                p.init(ctx.device)
        for d in DIRS:
            prev[d] = torch.zeros(ctx.K, ctx.S, dtype=torch.float64, device=ctx.device)
        if ctx_replace:
            jc.declare(ctx)

    hk.declare = declare
    low = [
        0.5 if any(op in ("ipw", "pace") for s in c.slots for op, _ in s) else 1.0 for c in cands
    ]
    qf = [c.qfl if c.qfl is not None else l for c, l in zip(cands, low)]
    return Monitor(
        tracks,
        ids=[c.hash for c in cands],
        q_floor=qf,
        combiner=c0.comb,
        w=[c.w or 0.5 for c in cands],
        hooks=hk,
        name=name,
        graph=graph,
    )


def compile(c: Candidate, **kw) -> Monitor:
    return compile_batch([c], **kw)
