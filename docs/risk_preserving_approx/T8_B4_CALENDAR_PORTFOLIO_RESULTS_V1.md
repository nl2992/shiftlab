# T=8, B=4 finite calendar-risk portfolio

Executed on 2026-10-29 under `T8_B4_CALENDAR_PORTFOLIO_PROTOCOL_V1.md` for the
exploratory low-persistence, high-signal cell selected from the registered B=4
grid. The finite bank contained 342 policies: 57 calendars at six working risk
levels. The exact master minimized cost subject to the conservative root-mixture
bound `sum_i w_i R_i <= 1/10`; singletons and all pairs were enumerated with exact
fractions. The selected portfolio used one component: calendar `[1,2,3,4]` at
working risk `1/10` with weight 1.

The optimizer-free verifier reconstructed the selected component behavior,
recomputed the behavioral portfolio under the unrestricted evaluator, and
checked exact expected metrics, full-history causal-null risk, the weighted-risk
bound and the finite-master minimum. All passed. Portfolio cost and risk are
`668697168881/195312500000` and `1/10`, exactly matching the best single
calendar. The decomposed reference costs `1666179899873/488281250000`, lower by
`11126044659/976562500000`.

This rules out a gain from this finite bank of risk-frontier calendar policies;
it does not rule out every possible randomized calendar controller or a denser
frontier. It strengthens the baseline while preserving scope: the portfolio is
a standard root lottery and does not establish methodological novelty. Exact
frontier rows, selected behavior records, source hashes and verifier are in
`t8_b4_calendar_portfolio_v1.json`, `calendar_portfolio_frontier.py` and
`verify_calendar_portfolio_frontier.py`. No real data or holdouts were accessed.
