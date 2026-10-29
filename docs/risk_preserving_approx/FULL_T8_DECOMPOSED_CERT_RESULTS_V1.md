# T=8 rational optimality bracket for the pre-promotion cap witness

Generated under `FULL_T8_DECOMPOSED_CERT_PROTOCOL_V1.md` on 2026-10-29. The
optimizer-free verifier passes and reconstructs the exact dual lower bound,
the full recovered policy and the independently saved `m=2` capped policy.

For `T=8`, `B=3`, `d=1`, transition `1/4`, emissions `(1/20,19/20)`,
`alpha=1/10`, query cost `1/100`, and switch cost `1/10`, the exact lower bound
is the large rational in `full_t8_decomposed_certificate_v1.json`, approximately
`3.864973906245213`. Both the full decomposed recovered policy and the cap policy
have exact cost `24735833/6400000 = 3.86497390625` and exact causal-null risk
`1/10`. The certified bracket width is `4.7869475491e-12` (relative width
`1.2385458907e-12`). Thus the `m=2` policy is certified within that amount of
the original unrestricted optimum, conditional on the proved first-promotion
decomposition and the exact sequence-form dual construction.

The verifier is optimizer-free but shares exact matrix and cost reconstruction
helpers with the generator, as the T=7 certificate verifier does. The registered
full generic sequence-form tree still does not finish at T=8; this certificate
is for the mathematically equivalent decomposed LP, not an independently built
generic tree. The cap's cost also matches the best of 64 calendars `[1,2,5]`.
This establishes an instance-specific compute/value result, not a strict cost
win over the calendar baseline, a general approximation theorem, or novelty.

Reproduction:

```powershell
uv run --no-sync python scripts/research_risk_approx/verify_full_t8_decomposed_certificate.py
```

The executed generator source is preserved at
`full_t8_decomposed_executed_source_v1.txt`; the tracked generator has only a
lint cleanup after its hash was recorded in the certificate.
