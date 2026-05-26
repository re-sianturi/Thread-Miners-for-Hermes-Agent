---
name: reels-script-writer
description: |
  Filters reel-ready candidates from scored.json, sorts by Evg.Score, takes
  top N (default 3), and drafts one reel script per candidate following
  reel-template.md. CTA is selected from cta-patterns.md based on the post's
  classification. Outputs one markdown file per reel into reels/.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [Social, Reels, Content, Writing]
---

# Reels Script Writer

Filters reel-ready candidates from scored.json, sorts by Evg.Score, takes
top N, and drafts one reel script per candidate following a template.

## When to Use

- After `threads-qa` validates the scored data.
- When you need 2-3 ready-to-record reel scripts per run.
- Called by the orchestrator — the final step before run-summary.

## Quick Reference

| Step | Script/Method | Input | Output |
|------|--------------|-------|--------|
| Select top | `select_top.py --run-dir DIR --max N` | `<run>/scored.json` | `<run>/top.json` |
| Draft reels | LLM per candidate | `top.json` + templates | `<run>/reels/reel-NNN.md` |

## Procedure

### Step 1: Select Top Candidates

```
python <skill_dir>/scripts/select_top.py --run-dir <run> --max <N>
```

Reads `scored.json` and filters by these criteria (ALL must hold):

- `classification` has `reel_ready: true` (from taxonomy.yaml)
- `15 <= len(hook) <= 80`
- `tot_int >= 30`
- `evg_score >= 1.0`
- `age_days <= 60`
- `media_format` in {Carousel, Gambar, Video}. Teks allowed only as
  fallback fill.

Takes top N by Evg.Score descending. Writes `<run>/top.json`.

If fewer than N candidates, logs shortfall and proceeds with whatever
passed. Does NOT relax the filter.

### Step 2: Draft Reel Scripts

For each entry in `top.json`:

1. Load `references/reel-template.md` and `references/cta-patterns.md`.
2. Pick CTA group matching the post's classification:
   - "Edukasi (Framework/Niche/Berita/Berita AI)" → Edukasi group
   - "Edukasi (Story)" → Edukasi Story group
   - "Tutorial (Pemula)" → Tutorial group
   - "Diskusi (Opini)" → Diskusi group
3. Prompt the LLM:

   ```
   You are a reels script writer for Instagram/TikTok.

   Source post:
   - Caption: <full caption>
   - Hook: <extracted hook>
   - Classification: <label>

   Write a reel script following the template.
   Constraints:
   - Hook ≤ 12 words, punchy, no filler
   - Body 150-220 words, 3-5 beats
   - Pick exactly one CTA from:
     <available CTAs from cta-patterns.md for this classification>
   - Do NOT fabricate stats, quotes, or data not in the source post
   - Use the exact template format from reel-template.md

   Output: complete markdown file content.
   ```

4. Validate output: hook ≤ 12 words, body 150-220 words, CTA from allowed
   list. If out of bounds: retry once with stricter instruction.
5. Write to `<run>/reels/reel-NNN.md` (NNN = 001, 002, ...).
6. Log LLM call to `<run>/trace/writer-<NNN>.json`.

## Pitfalls

- **Shortfall**: If fewer than 3 candidates pass the filter, don't relax
  thresholds. Surface the count to the orchestrator. The user can widen
  the date range or lower the floor explicitly.
- **CTA mismatch**: If classification doesn't match any CTA group (e.g.
  "Lainnya"), use the generic "Follow untuk konten serupa" as fallback.
- **Hook too long in script**: The hook field is ≤ 80 chars, but the
  script hook must be ≤ 12 words. These are different constraints — both
  must be satisfied.
- **Fabricated stats**: LLMs love adding "80% of users..." — the prompt
  explicitly forbids this. Check the output before saving.

## Verification

1. Confirm `TOP <N> of <M>` printed with N > 0.
2. Read `<run>/top.json` — verify each candidate passes all filter checks.
3. Check `<run>/reels/` — one file per candidate, named reel-NNN.md.
4. For each reel file: verify hook ≤ 12 words, body 150-220 words.
5. Confirm CTA is from the matched pattern group.
6. Check that no fabricated stats appear in the body text.
