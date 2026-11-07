"""Stage-2 baseline registry (PROTOCOL section 5).

REGISTRY[name] = (constructor, track, fidelity_class, notes); constructor() -> monitor with
``run(tape, keep_paths) -> Result``. ``track`` is the claim the baseline competes on (B, C or J).

Fidelity classes (docs/hgxh2c/01_BASELINE_AUDIT.md): SOURCE_REPRODUCED, SOURCE_FORMULA_VERIFIED,
TASK_ADAPTED, SOURCE_INSPIRED. All entries here are batched ports onto the common prediction-powered
event contract, so a published method is at best TASK_ADAPTED here even when its scalar formula was
verified in stage 1; HG/H2c/C1/C2 are SOURCE_REPRODUCED against the ShiftLab originals (tests, 1e-9).
Flags in ``notes``: DIFFERENT_NULL, EMPIRICAL_ALARM (not anytime-valid).

Anchor ports use exact-mode settings from docs/hgxh2c/00_ANCHOR_SPEC.md: gamma .995 (H2c, C1),
.99 (HG), cap 0.5, uniform cap Bd = hmax(1/q-1)+r0. Release semantics: HG, H2c, C1, C2 and all
others run with ``release="prefix"`` here (unqueried proxy increments arrive at once, the gap-closure
engine rule); the tests also run H2c/C1/C2 with ``release="legacy"`` (sota_search rule) to match the
originals, and HG with "prefix" against the gap engine.
"""

from __future__ import annotations

import torch

from shiftlab.hgxh2c.engines import (
    ClassicMonitor,
    Ctx,
    Hooks,
    Monitor,
    TrackSpec,
    VectorMixMonitor,
    ratio_guidance,
    sign_gate,
)  # fmt: skip

TS = TrackSpec


def hg(release="prefix"):
    """HG: Brier discounted Kelly (g=.99) gated by the sign of the discounted released cost increment."""
    return Monitor([TS("gC", ch="C", gamma=0.99, bet=False), TS("B", gamma=0.99)],
                   hooks=Hooks(stake={"B": sign_gate("gC")}), release=release, name="HG")  # fmt: skip


def h2c(release="prefix"):
    """H2c guided_disc: cost stake = Brier Kelly (g=.995) ratio re-expressed on the cost interval."""
    return Monitor([TS("gB", ch="B", gamma=0.995, bet=False), TS("C", gamma=0.995)],
                   hooks=Hooks(stake={"C": ratio_guidance("gB", "C")}), release=release, name="H2c")  # fmt: skip


def kelly(ch, gamma, release="prefix", name=None, **kw):
    return Monitor([TS(ch, gamma=gamma, **kw)], release=release, name=name or f"kelly_{ch}")


def ons(ch, release="prefix", name=None):
    return Monitor([TS(ch, base="ons")], release=release, name=name or f"ons_{ch}")


def xu_query(name):
    """Xu et al. variance policy: q proportional to sqrt(released residual second moment of the proxy bin)."""

    def f(ctx: Ctx, q):
        rv = ctx.res[name]
        tot = rv[1].sum(0)
        vbar = torch.where(
            tot > 0, rv[0].sum(0) / tot.clamp(min=1e-9), torch.full_like(tot, 0.0625)
        )
        return q * ctx.res_scale(name, ctx.h[name]) / vbar.clamp(min=1e-12).sqrt()

    return f


def xu(ch):
    return Monitor(
        [TS(ch, base="fixed", lam=0.5, bins=8)],
        hooks=Hooks(query=xu_query(ch)),
        q_floor=0.5,
        name=f"xu_{ch}",
        graph=True,
    )


def _solve3(A, g):
    """Cramer's rule for a batch of 3x3 systems: A [K,S,3,3], g [3,K,S] -> [3,K,S] (cheaper than linalg.solve)."""
    a = [[A[..., i, j] for j in range(3)] for i in range(3)]
    c = [
        a[1][1] * a[2][2] - a[1][2] * a[2][1],
        a[1][2] * a[2][0] - a[1][0] * a[2][2],
        a[1][0] * a[2][1] - a[1][1] * a[2][0],
    ]
    det = a[0][0] * c[0] + a[0][1] * c[1] + a[0][2] * c[2]
    x0 = (
        g[0] * c[0]
        + g[1] * (a[0][2] * a[2][1] - a[0][1] * a[2][2])
        + g[2] * (a[0][1] * a[1][2] - a[0][2] * a[1][1])
    )
    x1 = (
        g[0] * c[1]
        + g[1] * (a[0][0] * a[2][2] - a[0][2] * a[2][0])
        + g[2] * (a[0][2] * a[1][0] - a[0][0] * a[1][2])
    )
    x2 = (
        g[0] * c[2]
        + g[1] * (a[0][1] * a[2][0] - a[0][0] * a[2][1])
        + g[2] * (a[0][0] * a[1][1] - a[0][1] * a[1][0])
    )
    return torch.stack([x0, x1, x2]) / det


class JointContextualONS:
    """Strong control (2): stake_track = hi_track * clip(w_track . [1, u_B, u_C], 0, 1), u = relative Kelly
    position (min(K, hi)/hi) of each track on released data, w fitted by ONS on log(1 + lam x). Starts at
    w = e_own (= discounted Kelly), so cross-track terms are learned online. Hook object: ``hooks()``."""

    def __init__(self, names=("B", "C")):
        self.names, self.w, self.A, self._ctx, self.call = names, {}, {}, None, -1

    def declare(self, ctx):
        """(Re)initialise per-run state and aux buckets; called by the engine (Hooks.declare) or lazily on first use."""
        K, S, dev = ctx.K, ctx.S, ctx.device
        self._ctx, self.call = ctx, -1
        for i, n in enumerate(self.names):
            w = torch.zeros(3, K, S, dtype=torch.float64, device=dev)
            w[1 + i] = 1.0
            self.w[n] = w
            self.A[n] = torch.eye(3, dtype=torch.float64, device=dev).expand(K, S, 3, 3).clone()
            ctx.make_aux("g_" + n, (12, K, S))

    def _sync(self, ctx):
        if self._ctx is not ctx:
            self.declare(ctx)
        if ctx.call == self.call:
            return
        self.call = ctx.call
        K, S = ctx.K, ctx.S
        self.f = torch.stack(
            [torch.ones_like(ctx.base["B"])] + [ctx.base[n] / ctx.hi[n] for n in self.names]
        )  # [3,K,S]
        for n in self.names:
            v = ctx.collect("g_" + n)  # zeros when nothing arrived: A and w are then unchanged
            g, G = v[:3], v[3:].reshape(3, 3, K, S).permute(2, 3, 0, 1)
            self.A[n].add_(G)  # in place: state must keep its address under CUDA-graph capture
            self.w[n].copy_((self.w[n] + 2.2 * _solve3(self.A[n], g)).clamp(-1.0, 2.0))

    def stake(self, n):
        def f(ctx, lam):
            self._sync(ctx)
            return ctx.hi[n] * (self.w[n] * self.f).sum(0).clamp(0.0, 1.0)

        return f

    def after(self, ctx, Q, arr):
        for n in self.names:
            g = ctx.hi[n] * ctx.x[n] / (1.0 + ctx.lam[n] * ctx.x[n]) * self.f
            ctx.defer(
                "g_" + n, arr, torch.cat([g, (g[:, None] * g[None]).reshape(9, *g.shape[1:])])
            )

    def monitor(self, name="joint_ctx_ons", gamma=0.99):
        return Monitor([TS("B", gamma=gamma), TS("C", gamma=gamma)], combiner="bonf",
                       hooks=Hooks(stake={n: self.stake(n) for n in self.names}, after_step=self.after, declare=self.declare), name=name, graph=True)  # fmt: skip


def indep_hg_h2c():
    return Monitor(
        [TS("gC", ch="C", gamma=0.99, bet=False), TS("B", gamma=0.99),
         TS("gB", ch="B", gamma=0.995, bet=False), TS("C", gamma=0.995)],
        hooks=Hooks(stake={"B": sign_gate("gC"), "C": ratio_guidance("gB", "C")}),
        combiner="bonf", name="indep_HG_H2c",
    )  # fmt: skip


def fixed_mix(w):
    return Monitor(
        [TS("B", gamma=0.99), TS("C", gamma=0.995)], combiner="mix", w=w, name=f"mix_w{w}"
    )


def tenzer(kind, ch):
    if kind == "imputed":  # proxies treated as labels, no queries at all
        return Monitor(
            [TS(ch, proxy_only=True, factor="lrt", gamma=0.99)],
            frac=0.0,
            name=f"tenzer_imputed_{ch}",
        )
    corr = (
        "ipw" if kind == "lrt" else "pp"
    )  # lrt: observed labels only (Horvitz-Thompson); ppi: prediction-powered
    return Monitor([TS(ch, factor="lrt", corr=corr, gamma=0.99)], name=f"tenzer_{kind}_{ch}")


def _entry(fn, track, fid, notes=""):
    return (fn, track, fid, notes)


REGISTRY = {
    "HG": _entry(
        hg,
        "B",
        "SOURCE_REPRODUCED",
        "gap/sota_search anchor, prefix release; Brier null, cost gate",
    ),
    "H2c": _entry(
        h2c, "C", "SOURCE_REPRODUCED", "guided_disc g=.995; cost null, Brier-guided stake"
    ),
    "C1": _entry(
        lambda: kelly("C", 0.995, name="C1"), "C", "SOURCE_REPRODUCED", "discounted Kelly on cost"
    ),
    "C2": _entry(lambda: ons("C", name="C2"), "C", "SOURCE_REPRODUCED", "cost ONS"),
    "brier_kelly": _entry(
        lambda: kelly("B", 0.99, name="brier_kelly"), "B", "SOURCE_REPRODUCED", "HG without gate"
    ),
    "brier_ons": _entry(lambda: ons("B", name="brier_ons"), "B", "SOURCE_REPRODUCED", "ONS_Brier"),
    "timans_approx_C": _entry(
        lambda: Monitor([TS("C", base="grapa")], name="timans_approx_C"),
        "C",
        "TASK_ADAPTED",
        "approx-GRAPA scalar rule on PP increment mapped to [0,1], eps=.5, burn-in 100",
    ),
    "timans_approx_B": _entry(
        lambda: Monitor([TS("B", base="grapa")], name="timans_approx_B"),
        "B",
        "TASK_ADAPTED",
        "as above, Brier",
    ),
    "timans_grid_C": _entry(
        lambda: Monitor([TS("C", base="grapa_grid")], name="timans_grid_C"),
        "C",
        "TASK_ADAPTED",
        "grid-GRAPA lam in .1..1.9",
    ),
    "timans_grid_B": _entry(
        lambda: Monitor([TS("B", base="grapa_grid")], name="timans_grid_B"),
        "B",
        "TASK_ADAPTED",
        "grid-GRAPA, Brier",
    ),
    "csillag_C": _entry(
        lambda: Monitor([TS("C", corr="csillag", gamma=0.995)], name="csillag_C"),
        "C",
        "TASK_ADAPTED",
        "PP e-value factor; base stake adapts on queried labels only",
    ),
    "csillag_B": _entry(
        lambda: Monitor([TS("B", corr="csillag", gamma=0.995)], name="csillag_B"),
        "B",
        "TASK_ADAPTED",
        "as above, Brier",
    ),
    "xu_C": _entry(
        lambda: xu("C"),
        "C",
        "TASK_ADAPTED",
        "fixed stake .5*cap/Bd, variance-proportional active querying",
    ),
    "pprm_B": _entry(
        lambda: Monitor([TS("B", corr="eta", gamma=0.995)], name="pprm_B"),
        "B",
        "SOURCE_INSPIRED",
        "null differs (running risk, CM-EB CS in the paper); here betting on eta-PPI increment, eta from released window",
    ),
    **{
        f"tenzer_{k}_{c}": _entry(
            lambda k=k, c=c: tenzer(k, c),
            c,
            "SOURCE_INSPIRED",
            "DIFFERENT_NULL: Gaussian-LR e-factor / imputed labels",
        )
        for k in ("imputed", "lrt", "ppi")
        for c in "BC"
    },
    "pp_B": _entry(
        lambda: kelly("B", 1.0, name="pp_B"),
        "B",
        "TASK_ADAPTED",
        "task-compatible PP e-process: pooled (undiscounted) Kelly on the PP Brier increment, uniform cap",
    ),
    "pp_C": _entry(
        lambda: kelly("C", 1.0, name="pp_C"),
        "C",
        "TASK_ADAPTED",
        "pooled Kelly on the PP cost increment (C0 analogue)",
    ),
    "bonf_sep": _entry(
        lambda: Monitor(
            [TS("B", gamma=0.99), TS("C", gamma=0.995)], combiner="bonf", name="bonf_sep"
        ),
        "J",
        "TASK_ADAPTED",
        "separate Kelly tests, Bonferroni; the intersection alarm of Holm-in-time coincides with it",
    ),
    "holm_sep": _entry(
        lambda: Monitor(
            [TS("B", base="ons"), TS("C", base="ons")], combiner="bonf", name="holm_sep"
        ),
        "J",
        "TASK_ADAPTED",
        "separate ONS tests, Holm-in-time on two hypotheses (first step = Bonferroni on the intersection)",
    ),
    "joint_ctx_ons_full": _entry(
        lambda: JointContextualONS().monitor("joint_ctx_ons_full", gamma=1.0),
        "J",
        "TASK_ADAPTED",
        "full-history (undiscounted) contextual ONS",
    ),
    "ryu_wornell": _entry(
        VectorMixMonitor,
        "J",
        "SOURCE_INSPIRED",
        "mixture-portfolio vector bets on (B,C); fixed-grid mixture, formula unverified",
    ),
    "indep_HG_H2c": _entry(
        indep_hg_h2c,
        "J",
        "SOURCE_REPRODUCED",
        "HG and H2c side by side, Bonferroni, shared queries",
    ),
    "joint_ctx_ons": _entry(
        lambda: JointContextualONS().monitor(),
        "J",
        "TASK_ADAPTED",
        "each stake linear in both tracks' released Kelly positions, ONS-fitted",
    ),
    **{
        f"mix_w{w}": _entry(
            lambda w=w: fixed_mix(w),
            "J",
            "TASK_ADAPTED",
            "w*E^B + (1-w)*E^C, discounted Kelly each",
        )
        for w in (0.25, 0.5, 0.75)
    },
    **{
        f"{k}_{c}": _entry(
            lambda k=k, c=c: ClassicMonitor(k, c),
            c,
            "SOURCE_INSPIRED",
            "EMPIRICAL_ALARM: threshold = 95% quantile of null max (audit seeds); not anytime-valid",
        )
        for k in ("cusum", "ph")
        for c in "BC"
    },
}
