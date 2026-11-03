# Audit restart commands

Worktree: `shiftlab-retrospective-audit-2026-11-01`; branch `audit/shiftlab-retrospective-rectification-2026-11-01`; base `e74fdc33108d8e367094e57a46241a2b2e651caa`.

1. Read STATE.json, TASKS.md and both retained input documents.
2. Inspect `git status --short` and preserve every existing worktree.
3. Run `python scripts/retrospective_audit/source_census.py` to rebuild tracked branch/file census and unaudited decision candidates. This deliberately excludes ignored local outputs, PR-only records and files above 2 MB from decision text scanning; those remain separate required work.
4. Run `python -m pytest tests/test_seed_registry.py -q` (7 passed on initial run).
5. Complete W00 resource/local dirty-output snapshots before signing G00; then reconcile census candidates into scientific claims. Never mark candidate rows audited from regex hits alone.

Three attempted delegated reviewers failed at invocation with account usage limit. No independent signoff exists. Continue direct feasible analysis; retry separate reviewers when available. No scheduler has been configured and no future autonomous notification is promised.
