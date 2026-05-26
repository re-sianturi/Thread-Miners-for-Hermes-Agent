# Pipeline State Machine

The orchestrator tracks one state per run. State is persisted in
`config.yaml` (field: `status`).

## States

```
NEW → SCRAPING → SCORING → CLASSIFYING → QA → WRITING → COMPLETE
                                                         ↓
                                                      FAILED
```

| State | Description | Entry Action | Exit Condition |
|-------|-------------|-------------|----------------|
| `NEW` | Run folder created | new_run.py | Run dir exists |
| `SCRAPING` | Scraping keywords | scrape.py per keyword | All keywords scraped or failed |
| `SCORING` | Computing scores | score.py | scored.json written |
| `CLASSIFYING` | Hooks + LLM classify | extract_hook.py + LLM | classified.json written |
| `QA` | Validation + fix loop | validate.py | Pass or max 2 cycles |
| `WRITING` | Drafting reels | select_top.py + LLM | Reel files written |
| `COMPLETE` | Run finished | run_summary.py | Summary printed |
| `FAILED` | Non-recoverable error | — | Logged to run-summary.md |

## Recovery

If the orchestrator is interrupted mid-pipeline (e.g., session timeout):

1. Re-run `new_run.py` with the same args to create a fresh run, OR
2. Re-invoke the orchestrator skill — it detects existing run dirs by
   asking the user whether to continue from the last incomplete run.
3. State in `config.yaml` tells the orchestrator which step to resume from.

## Stop Conditions

- **API exhaustion**: After `len(keywords) * 10 + 5` API call attempts,
  aborts and transitions to FAILED.
- **QA max cycles**: After 2 fix cycles without full pass, transitions to
  COMPLETE with warnings.
- **Empty results**: If deduped.json is empty after filter, transitions to
  FAILED with "no posts matched your keywords/date range".
