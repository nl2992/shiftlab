# Compositor rules (search60)

`compositor.ComposedPolicy` wraps a parent (`eqsdp`: `Stage1C1Stop`, arm R lam .98 gamma .3 + cutoff H;
`wald`: `Stage2Wald` + cutoff H; `cutoff: null` = no cutoff) and runs modules. A module is
`compositor.Module` with `ID`, `FAMILY`, `DEFAULTS`, `SETTINGS` (two Phase-1 presets) and a `params` dict;
a spec is `{"modules": [{"id", "setting"?, "params"?}], "parent": {...}, "log": 0|1|2, "name"?}`.
Modules are registered with `@register`; `modules_A.py` ... `modules_F.py` are auto-imported when present.
Unknown params raise. A module whose class is not registered is `NOT_IMPLEMENTED`, never dropped.

## Information
Modules see only `Ctx`: t, predictions, remaining budget, pending (in-flight) labels with request times,
released purchased feedback (`FeedbackView`: event_id, t_requested, t_released, model_losses), the declared
contract (T, B, delay, cutoff) and the parent's evidence (n, k, deployed), which is built from released
labels only. `label`, `extra`, `query_probability`, `context` are not copied into any view (tested with
guarded proxies).

## Hook order
The simulator fixes release -> predict -> request. Within one event the compositor therefore runs:

1. `observe(due labels)`: for each label (sorted by event_id): parent evidence update (hook 2) ->
   `Module.on_release` (C belief overlays, A/B bookkeeping) -> if the parent flipped its deployment, a
   `Proposal` goes through `Module.on_switch_proposal` in precedence order E, F, D, C, B, A (hook 4);
   any `veto` reverts the flip.
2. `predict`: `Module.on_event` (hook 1, prediction-only monitors) -> parent.predict ->
   `Module.override_deploy` (hook 4; first non-None in the same precedence order wins; the parent's
   deployed state follows the final action) -> `on_deploy_change` notifications.
3. `request_labels` (hook 3):
   a. parent paced propensity `q` (budget view from the parent), then `Module.scale` multipliers
      (B17-B19 type, product, clipped to 1) give `q_final` for the parent's single draw. The draw is
      always consumed, exactly as the parent does.
   b. parent cutoff (`keep`) blocks a drawn purchase: `closed_blocked`.
   c. **Floors** (`Module.floor`, all called at every disagreement event with budget left):
      `lift` re-enables a cutoff-blocked drawn purchase; `force` buys regardless of the draw.
      Several overrides combine with **OR** (reasons and module ids are all logged). Both require the
      label to be releasable before T (t + delay < T). A purchase while the cutoff is closed is a
      logged `cutoff_exception`.
   d. **Gates** (`Module.veto`) can suppress a parent or lifted purchase; they cannot suppress a forced one.
   e. **Budget cap**: `Module.reserves` returns `Reserve(key, total, lo, hi)`. A purchase before a
      reserve window (t < lo) must leave its unused labels in the budget; a purchase inside the window
      draws it down; after hi it is released. The unused remainder of a reserve is summed across
      modules. B = 200 is also enforced by the simulator.
   Order of precedence for a quantity controlled by several modules: **safety floor, then gate, then
   budget cap.**
4. Logging (hook 5): `log=1` logs every disagreement decision and every switch proposal/override,
   `log=2` every event. Fields: `t, module_ids, p_parent, p_final, due, pending, remaining, evidence,
   kind, action, source, by, cutoff_exception, reason, closed` (+ `proposal` for switches).

## Conflicts
* One posterior engine: at most one of {C21, C24, C25, C26, C29, C30} (`UnsupportedCombo`,
  status `UNSUPPORTED_COMBO`, reason string; `eval60` writes it to `status.jsonl`).
* Duplicate module ids are `UNSUPPORTED_COMBO`.
* Scale multipliers multiply; vetoes OR; floors OR; reserves add; switch vetoes OR (any veto blocks);
  `override_deploy` is first-wins in precedence order E, F, D, C, B, A (safety first).
* The wrapped parent must be a `Stage1Base` family object whose `keep` is only the cutoff
  (`Stage1C1Stop`, `Stage2Wald`).

## All-off identity
With no modules, `request_labels` performs the same propensity call, `acq.note_event`, `min(1, q*mf)`,
one `rng.random() < q` draw and `keep` as `Stage1Base.request_labels`, and `observe` replays the parent
one label at a time (equivalent to its sorted batch loop). Module random streams are separate
(`policy_rng(seed_base, ep, "S60:<ID>")`), so enabling a module never perturbs the parent's stream.
