# Mechanism proposals: rollback and acquisition

Status: bounded development audit, 2026-11-06. This note does not register a confirmatory
claim or inspect any untouched confirmation outcomes.

## Existing mechanism audit

The repository already implements the key pieces under review:

| Component | Existing implementation | What it does | Remaining limitation |
|---|---|---|---|
| E_rb | `scripts/sota_sprint/fam_e.py::_rb` and `scripts/sota_sprint/fam_b.py::RecoveryMonitor` | Adds the Family B rollback wrapper to a certificate host; rollback uses a budget-left restart-mixture SR grid and a horizon gate. `E_rb` defaults to `alpha_rb_new=0.10`; `E_rb:...-a05` sets 0.05. | The host's label acquisition continues after promotion; rollback latency therefore competes with whatever budget remains. The claim is scoped to the stated conditional null and not serial dependence. |
| SRR/CUSUM and SR | `fam_e.py::SRRDetector`, `DetectorSwapMonitor`, `E_srr:*`, `E_srrSR:*` | Replaces the restart-mixture detector while preserving host, acquisition, switching flow, and budget. The implementation documents the ARL interpretation and lack of an anytime false-alarm bound for the per-start SRR statistic. | They are detector comparators, not certified substitutes for RMM's family-wise alarm control. |
| C2/C6 | `scripts/sota_sprint/fam_c.py` | C2 uses a shadow price to throttle labels; C6 adds deadline and two-stage acquisition controls. | Existing Family C ledger says C2's development gain does not replicate on its held-out check and fails at B=100; C6 is not significantly better than front-loading in the cited check. |
| Fixed reserve with rollback | `scripts/sota_sprint/fam_b.py::_make`, B5 | Reserves 15% of the query budget before a decision and adds rollback plus a deadline. | It changes both pre-promotion timing and post-promotion monitoring capacity, making attribution require B5 ablations. |
| No adaptive post-promotion acquisition | `fam_e.py::E_srr_noacq:*` | Disables the monitor's continued acquisition for the SRR detector swap. | It changes the detector and acquisition together relative to E_rb; interpret as a coarse ablation, not a clean acquisition-only contrast. |

Prior Family B ledger evidence already reports that reserve can delay or prevent promotion, and that
rollback helps on selected reversal regimes versus its host but loses against stronger certified
policies and on alternatives. Existing C2/C6 results similarly constrain any claim that label
economics alone repairs certification delay. See `docs/sota_sprint/family_b/ledger.json`,
`docs/sota_sprint/family_c/README.md`, and `docs/sota_sprint/novelty_audit.md`.

## At most one candidate considered

The only plausible joint design suggested by these mechanisms is **front-loaded acquisition plus
E_rb rollback**, optionally preserving a fixed reserve for post-promotion monitoring. Its components
are already present as front-loaded Gated acquisition (Family C), E_rb/B2 rollback, and B5's fixed
reserve/deadline wrapper. This is a conventional composition of known components, not a distinct
algorithmic contribution. No new policy was implemented. The development pilot below tests the
composition hypothesis through existing policies and ablations; it cannot establish novelty or
support confirmation.

## Mechanistic questions for the pilot

1. Does tightening rollback alpha from .10 to .05 reduce false reversals enough to offset slower
   reversal response under the matched label budget?
2. Does a per-label-start SRR/CUSUM or SR detector improve net cost over the restart-mixture detector
   when acquisition is held fixed?
3. Do continued post-promotion acquisitions or B5's pre-committed reserve provide useful rollback
   information, after charging all labels, switches, and predictive loss?

The pilot uses only synthetic development regimes already used in the project (`F3_reversal_800`,
`S_reversal_400`, `F4_recurrent`). They are not independent confirmation episodes.

**Scope correction after review:** the executed policy list does not contain a direct
front-loaded-acquisition-plus-E_rb arm. It compares existing E_rb, alpha .05, E_srr/CUSUM/SR,
no-acquisition, Family B B0/B2/B5, Gated, and never-switch arms. Therefore this pilot does not
falsify every possible joint schedule, tune the complete start-grid family, or isolate a full
acquisition × rollback factorial. It does falsify the claim that the tested E_rb wrapper itself
earns a distinct advantage in these regimes; combined with the prior-art audit and absence of a
surviving candidate, this bounded programme stops rather than adding unregistered arms.
