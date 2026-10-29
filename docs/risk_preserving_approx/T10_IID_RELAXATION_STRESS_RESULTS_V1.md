# T=10 IID-relaxation stress screen

On the registered T=10/B=4/d=2 low-persistence, high-separation synthetic cell,
the IID master used 13,421 learner variables, 4,868 flow equalities, one risk
row, no opponent variables and 10,813 builder nodes. It returned exact feasible
cost `51237636737353/12207031250000` (about `4.197387201524`) and exact
history-adaptive causal-null risk `1/10`. The exact rational dual lower bound is
`1820758244586013921892075323381623642341/433783722390811966429186910642298053880`.
The certified interval width is
`2014676972591299651037863331170361158241/132380286374149159676875888257537247888183593750000`,
about `1.52e-11`.

The robust decomposed reference completed on the same instance with the same
exact recovered cost and risk, 58,806 builder nodes and 13,790 null sequence
variables. The candidate has fewer builder nodes but took 114.84 seconds end to
end versus 58.01 seconds for the robust reference. Its saved process RSS delta
was about 40 MB versus 34 MB for the reference, so memory improvement is also
unestablished.

All 163 fixed calendars with at most four queries among slots 1–8 were solved
and exactly safety-calibrated. The best is `[1,2,3,4]`, cost
`20670239089321/4882812500000` (about `4.233264965493`). The candidate is lower
by exactly `875921971899/24414062500000` (about `0.03587776397`). This is a
reproduced synthetic economic win over exhaustive fixed-calendar baselines, with
a very narrow a-posteriori value certificate; the robust optimum is within the
reported lower/upper interval. The candidate does not improve the robust oracle's
cost and does not show a runtime or memory win.

## Branchwise risk certificate

The recovered policy has one random information state: after querying at events
1–3 and releasing positive labels at events 1 and 2, wait with probability `3/5`
or query at event 4 with probability `2/5`. The independent verifier split this
into two deterministic plans. Exhaustive checks over 1,024 tapes per plan found
zero violations on all 5,120 coordinatewise cover edges; their pathwise query
maxima are 3 and 4. The wait branch has exact IID and full-null risks `1/8`; the
fourth-query branch has risks `1/16`. Their root weights give exact risk
`(3/5)(1/8)+(2/5)(1/16)=1/10` and reproduce the saved alternative cost exactly.

For a deterministic plan whose first-promotion event is coordinatewise
increasing in the potential-label tape, couple each adaptively chosen null label
to an independent fair label using the same uniform random variable. Since the
null's conditional label probability is either 0 or 1/2, its label is no larger
than the fair label at every queried event; fill unqueried tape coordinates with
zero. Monotonicity gives null risk no greater than IID-tape risk. The IID fair
law belongs to the causal-null family, so the risks are equal. For an upfront
lottery over such branches, any fixed causal response has risk equal to the
weighted branch risks, and the same bound applies branchwise; taking the
supremum preserves the weighted bound. **PROVED**, conditional on this declared
causal-null family and the verified branchwise monotonicity. This is a useful
certificate for the recovered policy, not a novel optimization theorem.

The first verifier attempt omitted the decomposed post-promotion continuation
policy and failed with a missing-history error. That failed partial artifact and
traceback are preserved alongside the corrected verifier. The corrected run
supplies the continuation DP and passes all exact checks. Artifacts include
`iid_relaxation_t10_stress_v1.json`, its correction note,
`t10_iid_candidate_branchwise_v3.json`, and the protocol-bound scripts. Exact
T=10 stress and T=8 grid runner bytes used for the earlier outputs are preserved
as executed-source snapshots; the lint-clean branchwise verifier was rerun and
its current source hash is bound to the v3 output.
