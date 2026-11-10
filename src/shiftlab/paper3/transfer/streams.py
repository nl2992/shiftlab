"""Stream registry, domain families, sealed-group guard, causal early/eval episode split.

Data are read-only caches of the sibling checkout (paired 0-1 losses l0 = incumbent, l1 = challenger,
shape (K, 2000), plus constant label delay). Every stream was exposed by Papers 1/2: all results here
are EXPLORATORY. Sealed group: loading its arrays (other than for hashing in ``seal_hash``) raises
unless ``open_sealed=True`` is passed explicitly.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

DATA = Path(
    os.environ.get("P3_DATA_ROOT", "C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/data")
)
T = 2000
BUDGET = 200
EARLY_FRAC = 0.3  # first ceil(0.3 K) episodes (>=2) are the adaptation / feature window
MIN_EPISODES = 6

_311 = [
    "austin",
    "baltimore",
    "boston",
    "chicago",
    "cincinnati",
    "dallas",
    "dc",
    "denver",
    "kc",
    "louisville",
    "miamidade",
    "minneapolis",
    "nola",
    "oakland",
    "philly",
    "pittsburgh",
    "sacramento",
    "sandiego",
    "sf",
]

# name -> (directory, family)
REGISTRY: dict[str, tuple[str, str]] = {f"{c}_311": ("c4_sealed", "311") for c in _311}
REGISTRY.update(
    {
        "chicago_traffic_crashes": ("c4_sealed", "traffic_collision"),
        "montgomery_traffic": ("c4_sealed", "traffic_collision"),
        "nyc_collisions": ("c4_sealed", "traffic_collision"),
        "bts_ontime": ("c4_sealed", "aviation"),
        "airlines": ("saes_dev", "aviation"),
        "appliances": ("saes_dev", "uci_sensor"),
        "household_power": ("saes_dev", "uci_sensor"),
        "beijing_pm25": ("saes_dev", "uci_sensor"),
        "bike_hour": ("saes_dev", "uci_sensor"),
        "metro": ("saes_dev", "uci_sensor"),
        # singleton domains pooled into ONE fold; this is not a domain family
        "bank": ("saes_dev", "tabular_misc"),
        "elec2": ("saes_dev", "tabular_misc"),
        "rialto": ("saes_dev", "tabular_misc"),
        "weather": ("saes_dev", "tabular_misc"),
        "spam": ("saes_dev", "tabular_misc"),
        # sealed final-test group (three real domains, never evaluated in development)
        "austin_animal": ("c4_sealed", "animal_shelter"),
        "dallas_animal_shelter": ("c4_sealed", "animal_shelter"),
        "sf_building_permits": ("c4_sealed", "permits"),
        "la_crime": ("c4_sealed", "crime"),
    }
)
SEALED_FAMILIES = ("animal_shelter", "permits", "crime")
SEALED_GROUP_NAME = "civic_records_sealed"
SEALED_STREAMS = sorted(n for n, (_, f) in REGISTRY.items() if f in SEALED_FAMILIES)
DEV_FOLDS = ("311", "traffic_collision", "aviation", "uci_sensor", "tabular_misc")


class SealedAccessError(RuntimeError):
    pass


@dataclass
class Stream:
    name: str
    family: str
    l0: np.ndarray  # (K, T) int8 incumbent loss
    l1: np.ndarray  # (K, T) int8 challenger loss
    delay: int
    starts: np.ndarray

    @property
    def K(self) -> int:
        return self.l0.shape[0]

    @property
    def n_early(self) -> int:
        return max(2, int(np.ceil(EARLY_FRAC * self.K)))

    def early(self):
        return slice(0, self.n_early)

    def evalw(self):
        return slice(self.n_early, self.K)


def is_sealed(name: str) -> bool:
    return REGISTRY[name][1] in SEALED_FAMILIES


def path_of(name: str) -> Path:
    return DATA / REGISTRY[name][0] / f"{name}.npz"


def load(name: str, *, open_sealed: bool = False) -> Stream:
    if is_sealed(name) and not open_sealed:
        raise SealedAccessError(f"{name} belongs to the sealed final-test group")
    z = np.load(path_of(name), allow_pickle=False)
    return Stream(name, REGISTRY[name][1], z["l0"], z["l1"], int(z["delay"]), z["starts"])


def array_content_sha256(l0, l1, starts) -> str:
    return hashlib.sha256(l0.tobytes() + l1.tobytes() + starts.tobytes()).hexdigest()


def seal_hash() -> dict:
    """Hash of the sealed group: names plus array-content sha256 per stream (file bytes read only
    to hash; no loss statistic is computed)."""
    per = {}
    for n in SEALED_STREAMS:
        z = np.load(path_of(n), allow_pickle=False)
        per[n] = array_content_sha256(z["l0"], z["l1"], z["starts"])
    h = hashlib.sha256("|".join(f"{n}:{per[n]}" for n in sorted(per)).encode()).hexdigest()
    return {
        "group": SEALED_GROUP_NAME,
        "families": list(SEALED_FAMILIES),
        "streams": per,
        "group_sha256": h,
    }


def dev_streams(min_episodes: int = MIN_EPISODES) -> list[str]:
    """Eligible development stream names (sealed excluded; >= min_episodes)."""
    out = []
    for n, (_, f) in REGISTRY.items():
        if f in SEALED_FAMILIES:
            continue
        z = np.load(path_of(n), allow_pickle=False)
        if z["l0"].shape[0] >= min_episodes:
            out.append(n)
    return sorted(out)
