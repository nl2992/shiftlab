# Paper 4 TMLR draft: status

**Draft v0, 2026-11-21.** `main.tex` → `main.pdf` (17 pages, TMLR style copied from Paper 3, anonymised). Build with
`./build.sh` (latexmk). Compiles with no undefined or duplicate references and no overfull boxes. Nothing committed.

Every number in the paper is copied by hand from the lead-verified result records; the source file is named in a
comment above each table. The prose follows the academic-humanizer rules (no em-dashes, no hype vocabulary, each
claim tied to a table or theorem).

## Structure

1. Introduction (problem, adaptive null, premium, five contributions, scope)
2. Problem setup (rounds, labels, alternative, adaptive null, premium definition, one-label example)
3. RB-DP: risk recursion (Lemma 1), exact reduction (Thm 1), one-constraint corollary, dyadic lattice (Thm 2),
   exact finite programme, Algorithm 1, certified sandwich
4. Premium structure: persistent B = 1 zero premium (Prop 1), anti-persistent bounds (Thm 3 = M1, M4, M10, M11)
5. Synthetic experiments: E1 validation (190 cells), E2 scaling, E3 long-horizon premium, E4 baselines
6. Real streams: 35 datasets, 420-setting panel with P3c/P4c/P5r, census of 114, replay on 9,525 windows
7. Delay two
8. Related work, 9. Limitations, 10. Conclusion
Appendices: proofs of Lemma 1, Thm 1, Thm 2 and corollaries (complete); stress tests; structural results; full
premium curves; full E4 table; real-stream details and 35-dataset table; delay-2 programme.

## Open items before submission (red `[Draft: ...]` markers in the PDF; `\draftfalse` hides them)

1. **Proofs: done (2026-11-21)** in `app_structure.tex` (Appendix C): Lemma R, Prop 1 (Z1) in full; the one-label
   formula (N1), Lemmas S and Pre, and Thm 3(1) proved directly for c = k = 0 (simpler than SP1's general-k route);
   first-label relaxation (M3), Lemmas M4.1–M4.2 and Thm 3(2); Thm 3(4) (M11) in six steps; Thm 3(3) from parts 1, 2
   and the M6–M9 template. **Supplement obligation:** Thm 3(3) for B = 3–6 rests on exact rational enumeration;
   ship `prompts/26111216-{1,2,3,4}/constant_audit.py` (and outputs) in the anonymised supplement.
2. **Delay two: done (2026-11-21)** in `app_delay2.tex` (Appendix G): risk recursion, Bellman equations, solver
   validation, long-horizon table, and the list of what a full proof still needs.
3. **Dataset provenance:** Gutenberg ids for all 18 texts (only 6 recorded in `REAL_CHAINS.md`), UniProt accessions,
   citations for the promotion benchmarks, and the source record for `openml_ldpa` (also missing in Paper 3).
4. **Figures: done (2026-11-21)** in figures4papers style, chosen by the user: Fig. 1 risk-budget split
   (conceptual), Fig. 2 ρΓ(T) curves, Fig. 3 real-stream risk and replay cost. Scripts and provenance in
   `figures/README.md`; each script asserts its values against the paper's tables. Optional later: a delay-2 figure.
5. **Verify bibliography entries** marked `note = {verify}` in `refs.bib` (taken from memory or notes, not opened).
6. **Generate tables from result files** (a `make_tables.py` like Paper 3's) instead of hand-copied numbers, so the
   PDF is reproducible from `docs/paper4_continuation/rbdp/results/` and `real_data/results/`.
7. **Code release:** anonymised supplement with `src/shiftlab/paper4/risk_budget_dp_fast.py`, tests and the run
   scripts.
8. **Review:** a fresh-context review pass (as done for Paper 3) and a human read of Theorems 1–2.

## Framing decisions taken in this draft

- The 35-dataset result is the headline real-data claim; the census and replay are reported alongside it.
- The tie with the repaired i.i.d. planner (P5r) in replay is stated once, in §6 and in Limitations, with the census
  explanation (promotion streams are mostly persistent).
- Phase 3 streams excluded by the white-noise control are described in Appendix F, not counted.
