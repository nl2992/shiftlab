"""Stage 0 traced runner: per-event trace of the frozen simulator and a regret decomposition.

The simulator, policies and stream construction are reused unchanged from
``scripts/qsg_methods_search/sota_nine.py`` (``_job``) and ``scripts/failure_atlas_v2_flq/suite.py``
(``run_metrics``). The only additions are (i) extra Wald-family names registered through name
parsing and (ii) an evaluator-side decomposition of each run's regret over the best fixed model.

Decomposition (see 11_STAGE0_HEADROOM.md). For one run with deployed-model path ``dep``,
``n`` paid labels and ``sw`` switches (counted from the initial model 0):

    regret = J - J_hind,   J_hind = min(L0, L1),   J = loss + cq*n + cs*sw

* challenger-better episode (L0 > L1): J_hind = L1 and loss - L1 = sum_{dep=0}(l0 - l1) exactly
  (events on the challenger contribute 0). late_adoption = that sum; reversal_churn =
  cs*max(sw-1, 0); residual = cs*min(sw, 1), the unavoidable adoption switch.
* not-better episode (L0 <= L1): J_hind = L0 and loss - L0 = sum_{dep=1}(l1 - l0) exactly.
  false_promotion = that sum + cs*min(sw, 1) (the promotion switch); reversal_churn =
  cs*max(sw-1, 0); residual = 0.
* label_spend = cq*n in both cases.

Components sum to the regret exactly (up to floating-point summation of cq*n).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter")
for _p in (HERE, ROOT / "scripts/qsg_methods_search", ROOT / "scripts/failure_atlas_v2_flq"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

CQ, CS = 0.05, 5.0
REGS = {
    1: ("docs/qsg_methods_search/c4_registration.json", 2026111201),
    2: ("docs/qsg_methods_search/c4_registration_batch2.json", 2026111301),
}
NINE = {
    "sf_311": 1,
    "kc_311": 1,
    "montgomery_traffic": 1,
    "dallas_311": 1,
    "dc_311": 1,
    "austin_311": 2,
    "cincinnati_311": 2,
    "oakland_311": 2,
    "sandiego_311": 2,
}
WALD_LAMS = (0.9, 0.95, 0.97, 0.98, 0.99)
WALD_GAMMAS = (0.1, 0.2, 0.3, 0.5)
WALD_GRID = [f"wald_l{lam}_g{g}" for lam in WALD_LAMS for g in WALD_GAMMAS]
ARM_R = "EQSDp_l0.98_g0.3"
COMPONENTS = ["late_adoption", "false_promotion", "reversal_churn", "label_spend", "residual"]


def registry() -> dict:
    """EXTRA registry plus any Wald-family name missing from it (name parsing, no logic change)."""
    from hurdles import WaldLCB
    from sota_extra import EXTRA, _mk

    reg = dict(EXTRA)
    for name in WALD_GRID:
        if name not in reg:
            lam, g = name[len("wald_l") :].split("_g")
            reg[name] = _mk(WaldLCB, name, lam=float(lam), gamma=float(g))
    from stage1_policies import registry_entries  # Stage 1 candidates and controls (new names only)

    for name, f in registry_entries().items():
        assert name not in reg
        reg[name] = f
    return reg


def decompose(dep, l0, l1, n_labels, cq=CQ, cs=CS) -> dict:
    """Regret decomposition of one run; ``dep``, ``l0``, ``l1`` are length-T arrays."""
    dep = np.asarray(dep, dtype=int)
    l0 = np.asarray(l0, dtype=float)
    l1 = np.asarray(l1, dtype=float)
    sw = int(np.count_nonzero(np.diff(np.r_[0, dep])))
    loss = float(np.where(dep == 1, l1, l0).sum())
    L0, L1 = l0.sum(), l1.sum()
    j = loss + cq * n_labels + cs * sw
    regret = j - min(L0, L1)
    out = dict.fromkeys(COMPONENTS, 0.0)
    out["label_spend"] = cq * n_labels
    out["reversal_churn"] = cs * max(sw - 1, 0)
    if L0 > L1:
        out["late_adoption"] = float((l0 - l1)[dep == 0].sum())
        out["residual"] = cs * min(sw, 1)
    else:
        out["false_promotion"] = float((l1 - l0)[dep == 1].sum()) + cs * min(sw, 1)
    out.update(net=j, loss=loss, switches=sw, labels=int(n_labels), regret=regret)
    out["gap"] = regret - sum(out[k] for k in COMPONENTS)
    return out


def sealed_paths(main: Path = MAIN) -> dict:
    """name -> (npz path under the main checkout, delay, seed_base); verifies registered checksums."""
    out = {}
    for name, b in NINE.items():
        rel, sb = REGS[b]
        reg = json.loads((ROOT / rel).read_text())
        d = next(x for x in reg["datasets"] if x["name"] == name)
        assert reg["seed_base"] == sb
        p = main / d["sealed_path"]
        z = np.load(p)
        h = hashlib.sha256(z["l0"].tobytes() + z["l1"].tobytes() + z["starts"].tobytes())
        if h.hexdigest() != d["array_content_sha256"]:
            raise SystemExit(f"checksum mismatch for {name}")
        out[name] = (str(p), int(z["delay"]), sb)
    return out


def run_policies(names, losses, delay, ep, seed, seed_base, dataset, budget, check_orig=()):
    """Run named policies on one episode with the sota_nine rng derivation; return row dicts."""
    import c4_pilot
    from suite import build_suite, run_episode, run_metrics, stream_from_losses

    cfg = c4_pilot.CFG
    cq, cs = cfg["cq"], cfg["cs"]
    assert (cq, cs) == (CQ, CS)
    reg = registry()
    h = int.from_bytes(hashlib.sha256(dataset.encode()).digest()[:4], "big")
    T = losses.shape[0]
    gain = np.full(T, float((losses[:, 0].astype(int) - losses[:, 1]).mean()))

    def suite(ns):
        return build_suite(
            T, budget, cs, cq, cfg["alpha"], delay, ep * 100_000 + seed, seed_base + h % 1000,
            names=ns, extra=reg,
        )  # fmt: skip

    rows = []
    for pol in suite(list(names)):
        t_start = time.perf_counter()
        rng = np.random.default_rng([seed_base, h, ep, seed, 7])
        preds, labels = stream_from_losses(losses, rng)
        res = run_episode(
            pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
            label_price=cq, switch_cost=cs, trace=True,
        )  # fmt: skip
        secs = time.perf_counter() - t_start
        dep = np.fromiter((r["deployed_model"] for r in res.records), int, T)
        dec = decompose(dep, losses[:, 0], losses[:, 1], res.requested_labels, cq, cs)
        # the replicated bookkeeping must equal the simulator's own totals
        assert abs(dec["net"] - res.net_cost) < 1e-9, (pol.name, dec["net"], res.net_cost)
        assert abs(dec["gap"]) < 1e-9
        row = {
            "stream": dataset, "ep": ep, "seed": seed, "policy": pol.name, "budget": budget,
            "mean_gain": float(gain[0]), **{k: dec[k] for k in COMPONENTS},
            "net": res.net_cost, "loss": res.prediction_loss, "labels": res.requested_labels,
            "switches": res.deployment_switches, "regret": dec["regret"],
            "first_deploy": int(np.argmax(dep == 1)) if (dep == 1).any() else -1,
            "better": int(losses[:, 0].sum() > losses[:, 1].sum()), "secs": secs,
        }  # fmt: skip
        if pol.name in check_orig:  # untraced-path (original run_metrics) net for comparison
            (p2,) = suite([pol.name])
            m = run_metrics(
                p2, losses, gain, delay=delay, budget=budget, cq=cq, cs=cs,
                stream_rng=np.random.default_rng([seed_base, h, ep, seed, 7]),
            )  # fmt: skip
            row["net_orig"] = m["net"]
        rows.append(row)
    return rows


def job(args):
    dataset, path, delay, ep, seed, seed_base, names, budget, check_orig = args
    z = np.load(path)
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    return run_policies(names, losses, delay, ep, seed, seed_base, dataset, budget, check_orig)
