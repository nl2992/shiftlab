"""Worker-side registry patch for protocol C1: paper-formula ports and cutoff-equipped panel.

Importing this module (in every worker) makes ``trace_run.registry()`` also return
  * the four paper-formula ports and their H=1100 cutoff versions (baselines/paper_ports.py);
  * every panel comparator wrapped in CutoffWrapper(H=1100) under the name ``<comparator>_H1100``,
    except ``model_selector_causal`` (the wrapper is unsafe for it, docs 05 section 5).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for _p in (
    ROOT / "scripts/paper1_scale25/baselines",
    ROOT / "scripts/paper1_eqsdp",
    ROOT / "scripts/qsg_methods_search",
    ROOT / "scripts/failure_atlas_v2_flq",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np
import paper_ports as pp
import trace_run as tr
from analyze_all import ADAPTERS, CONTROLS

H = 1100
SOTA = ADAPTERS + CONTROLS
NOT_WRAPPED = ("model_selector_causal",)
CUT_NAMES = [f"{n}_H{H}" for n in SOTA if n not in NOT_WRAPPED]
PORT_NAMES = list(pp.registry_entries(H))


def _builtin_makers():
    """The panel members that live in suite.build_suite's own makers (same constructor calls)."""
    from cams import CAMSDeploymentAdapter, stack_advice
    from controls import EconomicReplacement
    from model_picker import ModelPickerDeploymentAdapter
    from online_llm_picker import OnlineLLMPicker
    from variance_min import VarianceMinStreamingIPW

    return {
        "model_picker_adapter": lambda T, B, cs, cq, a, d, r: ModelPickerDeploymentAdapter(
            2, 2, r("model_picker")
        ),
        "online_llm_picker": lambda T, B, cs, cq, a, d, r: OnlineLLMPicker(
            2, 2, rng=r("online_llm_picker")
        ),
        "cams_adapter": lambda T, B, cs, cq, a, d, r: CAMSDeploymentAdapter(
            n_models=2, n_classes=2, advice_fn=stack_advice(2, []), rng=r("cams")
        ),
        "variance_min_ipw": lambda T, B, cs, cq, a, d, r: VarianceMinStreamingIPW(
            2, 2, r("vmin"), rate=B / T, class_prior=np.array([0.5, 0.5])
        ),
        "economic_replacement": lambda T, B, cs, cq, a, d, r: EconomicReplacement(
            T, B, cs, rng=r("econ")
        ),
    }


def _extra_entries(base_reg):
    out = dict(pp.registry_entries(H))
    inner = {**_builtin_makers(), **{n: base_reg[n] for n in SOTA if n in base_reg}}
    for n in SOTA:
        if n in NOT_WRAPPED:
            continue
        f = inner[n]
        out[f"{n}_H{H}"] = lambda T, B, cs, cq, a, d, r, _f=f, _n=n: pp.CutoffWrapper(
            _f(T, B, cs, cq, a, d, r), T, d, H, name=f"{_n}_H{H}"
        )
    return out


def install():
    if getattr(tr, "_c1_installed", False):
        return
    orig = tr.registry

    def registry():
        base = orig()
        ex = _extra_entries(base)
        assert not set(ex) & set(base), set(ex) & set(base)
        return {**base, **ex}

    tr.registry = registry
    tr._c1_installed = True


install()
