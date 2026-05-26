---
name: threads-qa
description: |
  Validates the scored table after classification: deterministic checks
  first (arithmetic, schema, taxonomy membership, hook length), LLM fixer
  only as fallback. Outputs qa/report.yaml. If fixes are applied, also
  writes qa/fixes.yaml documenting what changed.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [QA, Validation, Threads]
---

# Threads QA

Validates the scored table after classification. Deterministic checks first
(arithmetic, schema, taxonomy, hook length). LLM fixer as last resort.

## When to Use

- After `threads-classifier` updates `scored.json`.
- Before `reels-script-writer` selects top candidates.
- Called by the orchestrator — validates data integrity at the pipeline's
  midpoint.

## Quick Reference

| Step | Script/Method | Input | Output |
|------|--------------|-------|--------|
| Validate | `validate.py --run-dir DIR` | `<run>/scored.json` | `<run>/qa/report.yaml` |
| LLM fix | Inline prompt | Report + scored.json | `<run>/qa/fixes.yaml` |
| Apply | `apply_fixes.py --run-dir DIR` | fixes.yaml | Updated scored.json + CSV |

## Procedure

### Step 1: Run Validation

```
python <skill_dir>/scripts/validate.py --run-dir <run>
```

- Runs all 12 checks (D1-D12) — see references/qa-checklist.md.
- Does NOT stop on first failure — collects all issues.
- Writes `qa/report.yaml` with full details.
- Exit 0 = all pass. Exit 1 = failures found.

### Step 2: If Failures — Classify

Read `qa/report.yaml`. Check `fixable_by_llm` and `fatal` lists.

- **Fatal** (D1, D8, D11, D12): Cannot auto-fix. Log to `run-summary.md`.
- **LLM-fixable** (D9, D10): Proceed to Step 3.
- **Script-fixable** (D2-D7): Re-run `score.py` to recompute arithmetic.

### Step 3: LLM Fix Cycle (max 2 cycles)

For each fixable check (D9, D10):

1. Read the offending rows from `scored.json`.
2. Prompt the LLM:

   ```
   Propose fixes for posts failing check D<N>.
   Constraint: <describe the rule, e.g. "hook must be ≤ 80 chars">

   Failing rows:
   <post_id>: <current value>

   Output JSON array:
   [{"post_id": "...", "field": "...", "after": "...", "reason": "..."}]
   ```

3. Validate proposals: `field` must be in whitelist (hook, tags,
   classification only). Reject any proposal changing numeric fields.
4. Write proposals to `<run>/qa/fixes.yaml`.
5. Run `apply_fixes.py --run-dir <run>`.
6. Re-run `validate.py`. If pass: done. If fail: one more cycle.
7. After 2 cycles max: stop. Log remaining issues to `run-summary.md`.

### Step 4: Handle D8 Separately

D8 (invalid classification label) is fatal — do NOT use LLM fixer.
Instead, re-run the classifier's LLM prompt for those specific rows
with a stricter instruction. Document the re-run in trace files.

## Pitfalls

- **False positives**: D12 (is_reply) is defense-in-depth; the filter
  should have removed all replies. If it fires, the filter step has a bug.
- **LLM fixer over-corrects**: The fixer might shorten hooks too much.
  Whitelist constraint prevents it from touching numeric fields.
- **Max 2 cycles**: Hard limit prevents infinite loops. If QA is still
  failing after 2 cycles, the orchestrator continues with logged warnings.
- **Empty scored.json**: If the pipeline produced no posts, all checks
  pass vacuously. The orchestrator should check count separately.

## Verification

1. Confirm `QA_PASS` or `QA_FAIL` printed with check details.
2. Read `qa/report.yaml` — verify passed list includes all expected checks.
3. If fixes were applied: check `qa/fixes.yaml` documents every change.
4. Re-read `scored.json` after fixes — confirm hook lengths ≤ 80, tags
   populated.
5. Re-run validate.py to confirm fix cycle resolved the issues.
