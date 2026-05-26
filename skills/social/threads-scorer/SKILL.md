---
name: threads-scorer
description: |
  Computes scoring metrics for each post in deduped.json: L, C, R, Tot.Int,
  Point (weighted), Viralitas, Eng.Density, Usia (Hari), Evg.Score. Pure
  deterministic Python. Outputs scored.json (full fields) and scored.csv
  (matches the user-facing column format exactly).
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [Social, Threads, Scoring, Analytics]
---

# Threads Scorer

Computes engagement scoring metrics for each post. Pure deterministic
Python — no LLM calls. Outputs both machine-readable JSON and
human-readable CSV.

## When to Use

- After `threads-scraper` produces `deduped.json`.
- Before `threads-classifier` adds hooks and topics.
- Called by the orchestrator — not typically invoked directly.

## Quick Reference

| Step | Script | Input | Output |
|------|--------|-------|--------|
| Score | `score.py --run-dir DIR` | `<run>/deduped.json` | `<run>/scored.json` + `<run>/scored.csv` |

Formulas documented in `references/formulas.md`.

## Procedure

1. Run the scoring script:
   ```
   python <skill_dir>/scripts/score.py --run-dir <run>
   ```
2. The script reads `<run>/deduped.json` and for each post computes:
   - `L`, `C`, `R`, `tot_int`, `point`, `viralitas`, `eng_density`,
     `age_days`, `evg_score`
   - `media_format` derived from API fields (Carousel/Video/Gambar/Teks)
   - `url` constructed from username + code
3. Writes `<run>/scored.json` with all fields, sorted by `evg_score` desc.
4. Writes `<run>/scored.csv` with user-facing columns, same sort order.

## Pitfalls

- **Age floor**: `age_days` is min 1 to prevent div-by-zero. Posts from the
  same day get `age_days=1` and the highest possible `evg_score` — this is
  intentional but means very fresh posts may rank aggressively.
- **Viralitas zero**: New posts with zero reshares get `viralitas=0%`. This
  is correct — don't treat it as an error.
- **Eng.Density N/A**: Posts with 0 likes get `eng_density = N/A`. This is
  valid — division by zero is undefined.
- **Unstable scores**: Posts < 7 days old haven't accumulated engagement
  yet. Their `evg_score` is provisional. Flag them in the run summary.

## Verification

1. Confirm `SCORED <N>` printed with N > 0.
2. Open `<run>/scored.csv` — verify columns match the spec order.
3. Spot-check a row: manually compute L+C+R and compare to Tot.Int. column.
4. Check that sorting is descending by Evg.Score.
5. Verify posts with 0 likes show "N/A" in Eng.Density column.
