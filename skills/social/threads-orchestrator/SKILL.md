---
name: threads-orchestrator
description: |
  Entry point for the Threads content-mining pipeline. Orchestrates scraping,
  scoring, classification, QA, and reel-script generation. Trigger phrases:
  "cari ide reel dari threads", "mining threads untuk konten", "buat reel
  dari threads tentang X", "scrape threads keyword Y", "find reel ideas from
  threads", "thread content mining for [topic]". Always use this skill
  instead of running scrape steps manually.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [Social, ContentMining, Threads, Orchestrator]
    related_skills:
      - threads-scraper
      - threads-scorer
      - threads-classifier
      - threads-qa
      - reels-script-writer
    config:
      - key: threads_miner.output_dir
        description: Where run artifacts are written
        default: "~/threads-miner-runs"
        prompt: Output directory for Threads Miner runs
required_environment_variables:
  - name: SCRAPECREATORS_API_KEY
    prompt: scrapecreators.com API key
    help: Get one at https://scrapecreators.com
    required_for: All scraping operations
---

# Threads Orchestrator

Entry point for the Threads content-mining pipeline. Coordinates 5
specialist skills to produce ready-to-record reel scripts.

## When to Use

Trigger this skill when the user says anything like:

- "cari ide reel dari threads"
- "mining threads untuk konten"
- "buat reel dari threads tentang X"
- "scrape threads keyword Y"
- "find reel ideas from threads"
- "thread content mining for [topic]"

Always use this skill instead of running scrape steps manually.

## Quick Reference

```
User input → orchestrator → [scraper → scorer → classifier → QA → writer] → run-summary.md
```

The orchestrator does NOT call subagents. It loads each specialist skill
via `skill_view`, executes its scripts sequentially, and passes state via
the run folder. See `references/pipeline.md` for full artifact flow.

## Procedure

### Step 1: Resolve output_dir

Read the `[Skill config: ...]` block injected at activation. Extract
`threads_miner.output_dir`. Expand `~` to the user's home directory.

If no output_dir is configured, use `~/threads-miner-runs` as default and
tell the user they can change it with:
`hermes config set skills.config.threads_miner.output_dir <path>`

### Step 2: Gather User Input

Ask for (in one batched question, not one at a time):

- **Keywords**: comma-separated list (required)
- **Date range**: start and end dates in YYYY-MM-DD format (required)
- **Max reels**: optional, default 3
- **Reel-readiness floor**: optional, default evg_score >= 1.0

If any are missing, ask in one message.

### Step 3: Create Run Folder

```
python <skill_dir>/scripts/new_run.py \
  --output-dir <resolved_output_dir> \
  --keywords <k1,k2,...> \
  --start <YYYY-MM-DD> \
  --end <YYYY-MM-DD>
```

Capture the absolute run path from stdout.

### Step 4: Scrape (load threads-scraper)

```
skill_view threads-scraper
```

For each keyword from the user input:

```
python <scraper_skill_dir>/scripts/scrape.py \
  --query "<keyword>" \
  --start <start> \
  --end <end> \
  --run-dir <run>
```

After all keywords are scraped:

```
python <scraper_skill_dir>/scripts/dedup.py --run-dir <run>
python <scraper_skill_dir>/scripts/filter.py --run-dir <run>
```

Check `<run>/deduped.json` — if empty, abort with message "No posts found
for your keywords/date range. Try different keywords or widen the range."

### Step 5: Score (load threads-scorer)

```
skill_view threads-scorer
python <scorer_skill_dir>/scripts/score.py --run-dir <run>
```

### Step 6: Classify (load threads-classifier)

```
skill_view threads-classifier
python <classifier_skill_dir>/scripts/extract_hook.py --run-dir <run>
```

Then run LLM classification in batches of 5 (see classifier SKILL.md for
the exact prompt). Write classifications + tags into scored.json.
Write classified.json for trace.

**IMPORTANT**: Classification delegation is NOT parallel — the orchestrator
runs the LLM prompts directly, one batch at a time, because Hermes doesn't
have subagents. Each LLM call is logged to `<run>/trace/classifier-N.json`.

### Step 7: QA (load threads-qa)

```
skill_view threads-qa
python <qa_skill_dir>/scripts/validate.py --run-dir <run>
```

If failures found:
1. Classify into fixable (D9, D10) and fatal (D1, D8, D11, D12).
2. For D2-D7: re-run `score.py` to recompute arithmetic.
3. For D9, D10: run LLM fixer (see qa SKILL.md prompt). Write fixes.yaml.
4. Run `apply_fixes.py --run-dir <run>`.
5. Re-validate. Max 2 cycles. If still failing: log to run-summary and
   continue with last-good state.

### Step 8: Write Reels (load reels-script-writer)

```
skill_view reels-script-writer
python <writer_skill_dir>/scripts/select_top.py --run-dir <run> --max <N>
```

Then for each candidate in `top.json`, draft a reel script via LLM (see
reels-script-writer SKILL.md for the exact prompt). Write to
`<run>/reels/reel-NNN.md`.

### Step 9: Generate Summary

```
python <skill_dir>/scripts/run_summary.py --run-dir <run>
```

### Step 10: Report to User

Print the absolute run path to the user.

## Delegation Note

This orchestrator uses **sequential file-based delegation**, not subagents.
Each specialist skill is loaded via `skill_view`, its procedure is executed,
and state flows via files in the run folder. This is intentional — it keeps
the main context clean, makes each step independently testable, and avoids
the complexity of subagent orchestration.

## Pitfalls

- **No subagents**: Unlike Claude Code's subagent-driven-development, the
  orchestrator loads skills sequentially into the same context. Each skill's
  instructions enter context momentarily and are replaced by the next. The
  run folder (`<run>/`) is the persistent state — keep it accessible.
- **API rate limits**: scrape.py retries 4 times with backoff. If all
  keywords fail, abort early rather than burning through the buffer.
- **LLM classification drift**: Each batch of 5 posts is a separate LLM
  call. Labels may drift between batches. The taxonomy validation step
  catches invalid labels but can't fix inconsistency within valid labels.
- **Orchestrator interrupted**: If the session is interrupted mid-pipeline,
  re-invocation should ask the user if they want to resume an existing run
  or start fresh. Check for existing `<run>/scored.json` etc.
- **Empty results**: If any step produces zero output (no posts, no reel
  candidates), surface this clearly instead of silently continuing.

## Stop Conditions

The orchestrator MUST enforce these:

1. **API call budget**: After `len(keywords) * 10 + 5` total API calls
   (including all scrape retries), abort and transition to FAILED.
2. **QA max cycles**: After 2 LLM fix cycles without full pass, continue
   with warnings. Do NOT loop forever.
3. **Reel shortfall**: If fewer than 3 reel-ready candidates survive the
   filter, emit 1-2 reels and surface the shortfall. Do NOT relax the
   filter automatically.
4. **Empty pipeline**: If deduped.json has 0 posts after filter, abort
   with a clear message. Don't waste LLM calls on empty data.

## Verification

Before reporting to the user, verify:

- [ ] `<run>/deduped.json` exists with N > 0 posts
- [ ] `<run>/scored.json` exists with correct arithmetic
- [ ] `<run>/scored.csv` has populated columns (Akun, Hook, Klasifikasi, Tags)
- [ ] `<run>/classified.json` has one entry per post
- [ ] QA passed or warnings are documented in run-summary.md
- [ ] `<run>/reels/` has at least 1 reel (.md) file
- [ ] `<run>/run-summary.md` exists with all counts
- [ ] API calls < budget limit
