"""The cached eval60 job path must return exactly the rows of the original ``trace_run.job``."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
for _p in (HERE, HERE / "search60"):
    sys.path.insert(0, str(_p))
import compositor as comp
import eval60 as ev60
import trace_run as tr

SPECS = [
    {"modules": [], "parent": {"kind": "eqsdp"}},
    {"modules": [{"id": "A01", "setting": 1}], "parent": {"kind": "eqsdp"}},
    {
        "modules": [{"id": "B11", "setting": 1}, {"id": "B16", "setting": 1}],
        "parent": {"kind": "wald"},
    },
]
FIELDS = ["net", "loss", "labels", "switches", "first_deploy", "regret", "late_adoption",
          "false_promotion", "reversal_churn", "label_spend", "residual", "better"]  # fmt: skip


def test_cached_job_equals_trace_job():
    ds, (path, delay, sb) = next(iter(tr.sealed_paths().items()))
    reg = comp.register_specs(SPECS)
    names = [*reg, "s2armr_H1100"]
    key = "t"
    for ep, seed in [(0, 0), (1, 1)]:
        base = (ds, path, delay, ep, seed, sb, names, 200, ())
        want = tr.job(base)
        for _ in range(2):  # second pass uses the warm caches
            got = ev60._job((base, reg, key))
            assert [r["policy"] for r in got] == [r["policy"] for r in want]
            for g, w in zip(got, want):
                assert all(g[f] == w[f] for f in FIELDS), (g["policy"], ep, seed)
    assert tr.registry.__name__ == "registry"  # the registry hook is restored after each job
