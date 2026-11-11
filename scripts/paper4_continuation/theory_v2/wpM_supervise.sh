#!/bin/bash
# Supervisor for the P3 mixing-scaling run (wpM_scaling.py). Runs detached from any agent session.
# - If the scaling job is not running and its outputs do not exist yet, relaunch it (it resumes from the partial file).
# - When the compact output exists, write MIXING_SCALING.md with the summariser and exit.
# - Holds idle sleep off (caffeinate -i) while alive; a closed lid still sleeps the Mac unless sleep is disabled.
# It never commits or pushes.
set -u
ROOT=/Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/shiftlab-methods-strategy-dba13e
SCR=/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad
export WPM_PARTIAL=$SCR/wpM_partial.jsonl
export WPM_PRI=v2
export WPM_WALL_S=${WPM_WALL_S:-10800}
COMPACT=$ROOT/docs/paper4_continuation/theory_v2/results/wpM_scaling_v1_compact.json
SUMMARY=$ROOT/docs/paper4_continuation/theory_v2/MIXING_SCALING.md
LOG=$ROOT/outputs/paper4_theory_v2/wpM_supervise.log
mkdir -p "$(dirname "$LOG")"
cd "$ROOT" || exit 1
caffeinate -i -w $$ &
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }
log "supervisor start pid=$$"
while true; do
  if [ -f "$COMPACT" ]; then
    if ! pgrep -f "theory_v2/wpM_scaling.py" >/dev/null; then
      if [ ! -f "$SUMMARY" ]; then
        .venv/bin/python scripts/paper4_continuation/theory_v2/wpM_summarize.py "$COMPACT" "$SUMMARY" >> "$LOG" 2>&1
        log "summariser exit=$? -> $SUMMARY"
      fi
      log "done; supervisor exit"
      exit 0
    fi
  elif ! pgrep -f "theory_v2/wpM_scaling.py" >/dev/null; then
    log "scaling job not running and no output yet: relaunching (resume from partial)"
    nohup nice -n 10 .venv/bin/python scripts/paper4_continuation/theory_v2/wpM_scaling.py \
      >> "$ROOT/outputs/paper4_theory_v2/wpM_scaling_run.log" 2>&1 &
  fi
  sleep 60
done
