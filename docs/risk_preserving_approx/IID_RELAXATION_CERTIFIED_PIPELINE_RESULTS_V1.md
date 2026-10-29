# IID-relaxation certified pipeline: T=8, B=4 screen

The preregistered IID-null LP found the same alternative cost as the full robust
reference on the low-persistence witness: `1666179899873/488281250000`. Its
recovered policy was already safe under the full history-adaptive causal null at
risk `1/10`, so the root-mixture repair had activation `1` and added no cost. The
best calendar and finite calendar portfolio remain at
`668697168881/195312500000`; the candidate preserves the reference's adaptive
gain but does not improve it.

The exact rationalized dual, including a reduced-cost residual correction, gives
lower bound
`33912681199052617326248234060483/9938258388540204617167802375000`. Together
with the independently recomputed exact feasible cost, the certified interval is
about `1.03e-9` wide. The IID risk row matched an independent fair-tape recursion;
the full-null recursion matched the framework verifier for raw and repaired
policies. Thus the safety and value interval are **PROVED for this finite
instance and this returned policy**, conditional on exact arithmetic in the
recorded LP matrices and the declared policy class. No general approximation
theorem follows.

The relaxed master used 3,869 learner variables, 1,276 flow equalities, one risk
row and no opponent variables, versus 3,869 learner and 4,973 null sequences in
the full reference. Its alternative-tree builder counted 3,441 nodes versus
17,922 reference nodes. End-to-end elapsed time was 10.11 seconds, compared with
5.39 seconds recorded for the full reference solve; therefore the smaller master
did **not** demonstrate an end-to-end runtime improvement. Peak RSS was not
available in the cross-run reference, so memory improvement is unestablished.
The current screen is mixed: strong cell-specific value certification and less
tree construction, but no calendar win and no measured total-resource win.

The method is a standard relaxation plus exact separation/repair pattern unless
a source-matched audit establishes a sharper novelty delta. Continue only as an
implementation candidate: profile coefficient construction and exact
verification separately, then test a preregistered paired synthetic set with
faithful baselines. Do not access CRSP or reserved holdouts before G1–G3. The
result JSON is `iid_relaxation_certified_pipeline_v1.json`; its protocol and
runner hashes bind the run to its registered inputs.
