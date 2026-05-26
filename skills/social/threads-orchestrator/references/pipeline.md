# Pipeline Overview

```
User request
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  threads-orchestrator                                       │
│  ─────────────────                                          │
│  1. Resolve output_dir from [Skill config]                  │
│  2. new_run.py → create timestamped folder                 │
│  3. skill_view threads-scraper → scrape + dedup + filter   │
│  4. skill_view threads-scorer → score                      │
│  5. skill_view threads-classifier → hook + classify + tags │
│  6. skill_view threads-qa → validate + fix                 │
│  7. skill_view reels-script-writer → select + draft        │
│  8. run_summary.py → final report                          │
│  9. Print run path to user                                 │
└─────────────────────────────────────────────────────────────┘
```

## Artifact Flow

Each specialist skill reads from and writes to the shared run folder.
State flows via files, not agent context.

```
new_run.py
    │
    ▼
scrape.py → raw/<keyword>.json          (N files)
    │
    ▼
dedup.py → deduped-pre-filter.json
    │
    ▼
filter.py → deduped.json
    │
    ▼
score.py → scored.json + scored.csv
    │
    ▼
extract_hook.py → scored.json (hook field)
    │
    ▼
LLM classify → scored.json (classification + tags)
    │
    ▼
validate.py → qa/report.yaml
    │
    ▼
[fix loop] → qa/fixes.yaml → apply_fixes.py → scored.json
    │
    ▼
select_top.py → top.json
    │
    ▼
LLM draft → reels/reel-NNN.md
    │
    ▼
run_summary.py → run-summary.md
```

## Why Sequential Delegation

Hermes does not have true subagents like Claude Code. The "delegation" in
this bundle is sequential: the orchestrator loads each specialist skill via
`skill_view`, executes its procedure, saves artifacts to disk, then proceeds
to the next. State flows via files in the run folder, not via agent context.
Main context stays clean because each specialist's SKILL.md only enters
context when invoked.

This is a deliberate design choice — sequential delegation with file-based
state is more reliable than parallel execution for a linear pipeline, and
each step is independently testable.
