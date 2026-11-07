## Shared context
This applies to every sprint-2 agent.

### Repo, branch and file rules
- Worktree: /Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/dazzling-wilbur-a3e951
- Branch: research/sprint2-a5b-d2-rmm, from main @ de9aaaa.
- Run everything from the worktree root with `uv run`. Read AGENTS.md.
- **No git state changes:** no commit, checkout, stash or reset. Other agents share this checkout.
- Write only your own files: your module, your tests, your docs folder, and your outputs folder (outputs/ is gitignored).

### Read first
- docs/sprint2/SPEC.md
- scripts/sota_sprint/bench2.py
- scripts/sota_sprint/risk_curves.py
- docs/sota_sprint/REPORT.md
- docs/sota_sprint/publication_register.md

### Harness (frozen; do not edit shared files)
Policies use the factory signature `f(T, B, cs, cq, alpha, delay, r) -> Policy`, where `r(name)` is a private generator. Expose them as `EXTRA = {name: factory}` in your module. scripts/sota_sprint/registry.py autoloads fam_h, fam_r, fam_t, fam_p, fam_e and fam_f.

Paired runner:
```
uv run python scripts/sota_sprint/screen.py --regimes R1,R2 --policies P1,P2 --seeds 20 \
  --seed-base 2026110701 --workers 2 [--alpha 0.05] [--kind real] --out outputs/sprint2/<you>/<run>
```
- Use `--workers 2`; seven agents share 10 CPUs.
- `--kind real` regimes:
  - cached real streams: rialto, openml_ldpa, airlines, criteo, bank, elec2, weather, spam, uci_occupancy
  - fresh streams: metro, beijing_pm25, bike_hour, appliances, household_power
  - known-null twin streams: twin_<fresh name>
- Synthetic regimes: bench.DEV_ENVS, plus validation_spec.NEW (W_*) and ooc_regimes.OOC (O_null_semimarkov, O_null_order2). Atlas V_* regimes are also available.
- Contrasts: `uv run python scripts/sota_sprint/analyze.py DIR --candidates X,Y --hosts X=host --out PATH.json`
- Track R: run every candidate and its comparator at each alpha in bench2.ALPHA_GRID.
  - Development: seed base 2026110701 on bench2.RISK_NULLS + RISK_ALTS.
  - Evaluation: seed base 2026110711.
  - Then: `uv run python scripts/sota_sprint/risk_curves.py --dev DEVDIRS --eval EVALDIRS --out PATH`
- Track V: in your ledger, state which null each method tests (V1 conditional advantage, V2 marginal stationary Markov, V3 economic non-improvement, or none). Never compare a conditional error rate with a marginal error rate as if they were the same hypothesis.
- Policy protocol: scripts/promising_directions/sota/simulator.py. Propensities are frozen at issue; labels arrive after the delay.

### Sprint-1 facts you must use
- **D2.** fam_d.DeployGate(host=CAMS) with `cert=started_mixture` (QSG's StartedMixture, iid conditional null). fam_d's cert interface is `cert(side)` returning an object with `update(z, event_t, last)`.
  - A1/A5b evidence is fam_d._A1Cert(side, fam_a.MarkovSUI, **fam_a._B).
  - D5 = D2 with A1 evidence (default kwargs). In development D5 was safe but lost most of its power.
  - D2's real-data advantage: it beat the best certified port on 4/5 fresh datasets. Its synthetic superiority did not replicate. It promoted .20-.23 on the rho=.8 null and .27/.18/.56 on twin nulls.
- **A5b.** fam_a.FamA(evidence="sui", density="adaptive", rho_sig=2.0, sui_kw=fam_a._B).
  - Valid under a stationary first-order Markov null for any rho. Twin-null real rates were .000-.058.
  - Its free-rho composite null absorbs persistent evidence: only sign changes count, so a long winning run looks like persistence. Real-data power loss is heavy on appliances, beijing and household, and lighter on bike and metro.
- **RMM (Amendment 5, registered PASS).** On 4 certificate hosts it cut cost by -14.5 to -47.2 vs host, and beat Xu on late improvement by -15 to -30.
  - Fails: rho=.8 nulls .12-.18, twin nulls .14-.62, and reversals.
- **The failed merge (Amendment 6, scripts/sota_sprint/fam_m.py).** The SUI restart detector kept only 13-22% of RMM's late gain and failed real twin-null validity. The mechanisms:
  - the free-rho null absorbs regime runs;
  - the A5b host spends the budget before the detector gets evidence;
  - restart starts add real-data risk.
- **Choe-Ramdas port.** `choe_ramdas_eb` is DiscernQCE, i.e. PrPl-EB on query-conditional ±1 outcomes. On ±1 outcomes, the betting e-process prod(1 + lambda·x) equals the Bernoulli likelihood-ratio mixture used by QSG's StartedMixture. A faithful Choe-Ramdas / Henzi-Ziegel method tests the time-averaged conditional mean of paired loss differences over ALL events. Under a label budget that needs IPW, cf. gated_deployment.
- **Twin-null finding.** Promotions there are mostly toward the twin that realised lower loss in that episode, so harm is small. The violation is of the marginal guarantee, not a large economic loss.
- **Comparators:**
  - certificate methods/ports: gated_deployment, gated_adaptive_range, gated_adaptive_range+front, discern_style (corrected), discern_design_floor, SMCS+retain-incumbent, choe_ramdas_eb(+front), gated_deployment+QCE(+front)
  - acquisition adapter: xu_acquisition_only (Xu acquisition plus ShiftLab paired V1 certificate; not Xu's published certificate)
  - uncertified: model_picker_adapter, cams_adapter, model_selector_causal, online_llm_picker, variance_min_ipw, gong_zhang_paid_obs, qiu_delayed_movement, ryabchenko_capacity
  - controls: economic_replacement, CONTROL_never_switch
  - internal: QSG, A5b, D1, D2, D5, rmm:*, M_* (fam_m)

### Requirements for every candidate you own
- Executable code plus unit tests in tests/sprint2/test_<module>.py. They must cover: budget never exceeded, null behaviour on short streams, and the mechanism itself.
- A real paired screen: >= 20 development seeds at base 2026110701 on >= 4 environments. Two must be targeted, one null/adverse, and one outside the candidate's intended region.
- Real-stream development runs where applicable.
- A mechanism ablation.
- Track E, R and V results.
- A ledger entry in docs/sprint2/<your folder>/ledger.json. It is a list of objects with the fields:
  id, status (TEST_FAILED / SCREENED_NEGATIVE / SCREENED_PROMISING / BLOCKED), implementation (file:class), run_config (exact commands), seed_manifest, results_artifact, track_E, track_R, track_V, ablation, disposition, next_action.

### Rules
- Never fabricate numbers.
- Report negative results plainly.
- Development evidence is not validation.
- Never claim an empirical risk level is a guarantee.
- Episode runtime must be under ~1.5 s.

### Final message
Under 600 words:
- a table of your candidates with status and key numbers for Tracks E, R and V
- the 1-2 mechanisms you would advance to Round 5, with the exact policy names
- paths to your files
