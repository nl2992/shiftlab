import numpy as np

from shiftlab.paper3.payback.certificates import *
from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.sim import *

env = Envelope(v=0.002)
spec = Spec(T=300, B=150, d=5, h=30, k=3.0, alpha=0.1, env=env)
print(plan_batch_size(env, 0.05, 150))
mk = {
    "B2": lambda: B2Certificate(env, spec.alpha),
    "B1": lambda: B1Certificate(env, spec.alpha),
    "B1n": lambda: B1NaiveContinuation(env, spec.alpha),
    "B0a": lambda: B0Window(env, spec.alpha, 60),
    "B0b": lambda: B0Forecast(env, spec.alpha, 60),
}
for kind in ["drift", "boundary", "stress_reversal"]:
    for name, f in mk.items():
        rs = [run_one(spec, *make_stream(kind, spec, (SMOKE_BASE, 1, i)), f) for i in range(100)]
        c = [r for r in rs if r["certified"]]
        print(
            kind,
            name,
            len(c),
            np.mean([r["wrong"] for r in c]) if c else None,
            np.mean([r["t"] for r in c]) if c else None,
        )
