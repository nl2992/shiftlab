"""Factories for the in-repo Atlas-harness comparators (WP1e). NEW glue module, no ported logic.

Everything here is a thin registry over code that is either (a) already in this branch's base
(``main@7354480a``: ``shiftlab.dive``) or (b) ported unchanged into this package from
``origin/research/gave-r-2026-11-06`` (``gapmix``, ``pave``, ``freshcheck``, ``integrated``,
``erb_port``). Every factory returns a ``shiftlab.dive.switching_explore.Method`` (protocol
``start(cfg)`` / ``step(t, released) -> (action, query)``) which the Atlas harness or
``bench/contract/adapters_inrepo.py`` drives.

Entries: name -> (factory, MethodInfo). ``MethodInfo.null`` is the null the method's own source
documents ('cond' = conditional-mean null E[-D_t - h | F_{t-1}] <= 0 for bounded D, under the
declared dependence class; never 'marg' or 'abs_risk' for these gates). See
docs/d2a_rar/baselines/INREPO_PORTS.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import atlas_dependence_baselines as adb
from shiftlab.dive import switching_explore as se
from shiftlab.dive.switching_explore import Method
from shiftlab.sota.inrepo import erb_port, freshcheck, gapmix, integrated, pave


@dataclass(frozen=True)
class MethodInfo:
    source: str  # where the code lives (ref or HEAD path)
    outputs: tuple[str, ...]  # subset of alarm/certificate/label_allocation/promotion/rollback
    null: str  # registry target_null: 'cond' | 'marg' | 'abs_risk' | 'econ' | 'none'
    registry_id: str = ""  # id in docs/d2a_rar/registry/null_assumptions.yaml
    note: str = ""


_GAVER = "origin/research/gave-r-2026-11-06"
_DIVE = "main@7354480a src/shiftlab/dive"
_PR = ("promotion", "rollback")
_LPR = ("label_allocation", "promotion", "rollback")


# Gap-Mix registry names -> (null, registry id): exact/env are declared-Markov (marg) nulls,
# mlr_default8 is the Markov-LR comparator (marg), the iid/thin variants are the cond-null e-process.
_GAPMIX_NULL = {
    "exact0.8_s4": ("marg", "gap_mix"),
    "env0.8_s4": ("marg", "gap_mix"),
    "mlr_default8": ("marg", "markov_lr"),
    "thin10_s4": ("cond", "thinned_hedged_gate"),
    "thin4_s4": ("cond", "thinned_hedged_gate"),
    "iid_s4": ("cond", "episode_front"),
    "iid_repo32": ("cond", "episode_front"),
}


def _reg() -> dict[str, tuple[Callable[[], Method], MethodInfo]]:
    r: dict[str, tuple[Callable[[], Method], MethodInfo]] = {}
    # ---- Gap-Mix family (declared stationary two-state Markov chain, rho_bar declared)
    for n in (
        "exact0.8_s4",
        "env0.8_s4",
        "thin10_s4",
        "thin4_s4",
        "iid_s4",
        "iid_repo32",
        "mlr_default8",
    ):
        r[f"gapmix:{n}"] = (
            lambda n=n: gapmix.build_gate(n),
            MethodInfo(
                f"{_GAVER}:src/shiftlab/gaver/gapmix.py",
                _PR,
                *_GAPMIX_NULL[n],
                "episode_front gate (calendar, alpha spending, econ_ok, window-mean rollback)",
            ),
        )
    # ---- Markov-LR / thinned gates (already in base)
    r["markov_lr_gate"] = (
        lambda: adb.build_dep("markov_lr_gate"),
        MethodInfo(
            f"{_DIVE}/atlas_dependence_baselines.py",
            _PR,
            "marg",
            "markov_lr",
            "Markov skeleton treated as homogeneous; D binarised by sign",
        ),
    )
    r["thinned_hedged_gate"] = (
        lambda: adb.build_dep("thinned_hedged_gate"),
        MethodInfo(
            f"{_DIVE}/atlas_dependence_baselines.py",
            _PR,
            "cond",
            "thinned_hedged_gate",
            "gap-10 thinning; lag-10 independence assumed, not proved",
        ),
    )
    # ---- episode_front and relatives (Page-CUSUM rollback lives in the ComposedMethod / _FrontGated shells)
    r["episode_front"] = (
        lambda: se.build_method("episode_front"),
        MethodInfo(
            f"{_DIVE}/switching_explore.py",
            _PR,
            "cond",
            "episode_front",
            "alpha all in episode 0; econ_ok; window-mean rollback",
        ),
    )
    r["episode_geo"] = (
        lambda: se.build_method("episode_geo"),
        MethodInfo(
            f"{_DIVE}/switching_explore.py",
            _PR,
            "cond",
            "episode_front",
            "geometric alpha spending over episodes",
        ),
    )
    r["page_cusum_default"] = (
        lambda: freshcheck.make_method("existing_cusum"),
        MethodInfo(
            f"{_GAVER}:freshcheck.make_method('existing_cusum') over {_DIVE}/atlas_components.py",
            _PR,
            "none",
            "page_cusum",
            "repo default spec: uniform calendar + Page-CUSUM rollback (kappa=2); "
            "rollback is an EMPIRICAL_ALARM (not anytime-valid)",
        ),
    )
    # ---- DSS / straddle (frozen cycle-7 candidate)
    r["dss"] = (
        lambda: comp.build_candidate(comp.dss_spec(4, True)),
        MethodInfo(
            f"{_DIVE}/atlas_components.py (dss_spec(4, True), spec id 5b5c77b635e5)",
            _LPR,
            "cond",
            "dss_straddle",
            "straddle/undecided-only acquisition; delay switch -> uniform when d >= P*T/(B+P)",
        ),
    )
    r["straddle"] = (
        lambda: comp.build_candidate(
            next(
                sp
                for ax in (
                    "onset",
                    "duration",
                    "s",
                    "d",
                    "budget_frac",
                    "effect",
                    "rate",
                    "unknown",
                )
                for sp in comp.propose_candidates(ax, max_n=60)
                if sp.spec_id == comp.DSS_SOURCE_ID
            )
        ),
        MethodInfo(
            f"{_DIVE}/atlas_components.py (spec b1a17927d9ad, undecided-only)",
            _LPR,
            "cond",
            "dss_straddle",
            "",
        ),
    )
    # ---- PAVE and delay-gated PAVE (+ Gap-Mix x PAVE factorial)
    r["pave_full"] = (
        lambda: pave.PaveMethod(pave.PaveParams()),
        MethodInfo(
            f"{_GAVER}:src/shiftlab/gaver/pave.py",
            _LPR,
            "none",
            "pave",
            "PAVE dataclass defaults: reserve on, kappa .05, q .002",
        ),
    )
    r["pave_tuned"] = (
        lambda: pave.PaveMethod(integrated.PAVE_TUNED),
        MethodInfo(
            f"{_GAVER}:src/shiftlab/gaver/pave.py",
            _LPR,
            "none",
            "pave",
            "reserve off, kappa .1, q .03 (WP2 dev-tuned)",
        ),
    )
    for ev in integrated.EVIDENCES:
        for aq in integrated.ACQS:
            nm = f"gaver:{ev}:{aq}"
            r[nm] = (
                lambda nm=nm: integrated.build(nm),
                MethodInfo(
                    f"{_GAVER}:src/shiftlab/gaver/integrated.py",
                    _LPR,
                    "none",
                    "pave",
                    "DSS shell; acq=pave is the DELAY-GATED PAVE (active iff d >= 2T/(B+2))",
                ),
            )
    # ---- FreshCheck family, E_rb port, two-phase persistence
    for n in (
        "fresh_reserve",
        "fresh_noreserve",
        "reuse_noreserve",
        "paced_cost_threshold",
        "paced_cusum",
    ):
        r[f"freshcheck:{n}"] = (
            lambda n=n: freshcheck.make_method(n),
            MethodInfo(
                f"{_GAVER}:src/shiftlab/gaver/freshcheck.py",
                _PR,
                "cond" if n.startswith("fresh") else "none",
                "freshcheck" if n.startswith("fresh") else "",
                "FreshCheck: fresh post-switch e-process at alpha_rb (keep-null E[-D|F]>=h)"
                if n.startswith("fresh")
                else "heuristic comparator mode of the same shell (no rollback guarantee)",
            ),
        )
    r["erb"] = (
        lambda: erb_port.make("erb"),
        MethodInfo(
            f"{_GAVER}:src/shiftlab/gaver/erb_port.py (detector logic of origin/codex/sprint2-leaderboards "
            "scripts/sota_sprint/fam_b.py / fam_e.py)",
            _PR,
            "cond",
            "e_rb",
            "E_rb detector logic only; the sprint event-stream host is not ported",
        ),
    )
    r["erb_a05"] = (lambda: erb_port.make("erb_a05"), r["erb"][1])
    r["two_phase"] = (
        lambda: erb_port.make("two_phase"),
        MethodInfo(
            f"{_GAVER}:erb_port.TwoPhaseMethod (online adaptation of {_DIVE}/persistence_promotion.py "
            "_two_phase_decisions)",
            ("promotion",),
            "cond",
            "two_phase_persistence",
            "intersection-union of two e-processes in successive windows; no rollback",
        ),
    )
    return r


REGISTRY = _reg()
NAMES = tuple(REGISTRY)


def build(name: str) -> Method:
    if name not in REGISTRY:
        raise KeyError(f"unknown in-repo method {name!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[name][0]()


def info(name: str) -> MethodInfo:
    return REGISTRY[name][1]
