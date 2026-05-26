---
name: threads-classifier
description: |
  For each post: extract Hook (deterministic, first sentence < 80 chars),
  classify topic from references/taxonomy.yaml (LLM, must pick from list),
  and generate Tags (algorithmic tags from API + 3-7 content keywords from
  LLM). Updates scored.json and regenerates scored.csv with the new fields
  populated.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [Social, Threads, Classification, LLM]
---

# Threads Classifier

For each scored post: extract Hook (deterministic), classify topic (LLM
using taxonomy.yaml), generate Tags (algorithmic + LLM keywords).

## When to Use

- After `threads-scorer` produces `scored.json`.
- Before `threads-qa` validates the output.
- Called by the orchestrator — populates three fields: hook, classification,
  and tags in scored.json + scored.csv.

## Quick Reference

| Step | Method | Input | Output |
|------|--------|-------|--------|
| Extract hook | `extract_hook.py` (deterministic) | `<run>/scored.json` | Updates hook field |
| Classify topic | LLM, batch of 5 posts | `taxonomy.yaml` labels | Updates classification field |
| Generate tags | LLM + algorithmic | API fragments + LLM | Updates tags field |
| Save | Python | Updated scored.json | classified.json, trace/

## Procedure

### Step 1: Extract Hook (deterministic)

```
python <skill_dir>/scripts/extract_hook.py --run-dir <run>
```

The script takes the first sentence of each post's caption. If longer than
80 chars, truncates at the last word boundary before 77 and appends "..."
If shorter than 15 chars, takes the first 80 chars of the full caption.

### Step 2: Classify Topic (LLM)

1. Load `references/taxonomy.yaml`. Extract the list of `categories[].label`.
2. Read `scored.json`. Group posts into batches of 5.
3. For each batch, prompt the LLM:

   ```
   Classify each post into exactly one label from the list below.
   If no label fits, use "Lainnya".
   Output JSON array: [{"post_id": "...", "label": "..."}]

   Available labels: <comma-separated list>

   Posts:
   <post_id_1>: <caption text truncated to 500 chars>
   <post_id_2>: <caption text truncated to 500 chars>
   ...
   ```

4. Validate each returned label is in the taxonomy list:
   - If valid: assign to post.
   - If invalid: retry that post once with stricter prompt. If still invalid:
     set to `Lainnya` and log to `flagged` list (included in run-summary.md).
5. After all batches: write classifications into `scored.json`.

### Step 3: Generate Tags

Two-pass approach:

**Algorithmic tags** (deterministic, no LLM): Extract from
`text_post_app_info.text_fragments.fragments[]` where
`fragment_type == "tag"`. These are the hashtags the post author used.

**Content keywords** (LLM): In batches of 10, prompt:

```
Extract 3-7 lowercase keywords from each post's caption.
Output JSON object: {"<post_id>": ["keyword1", "keyword2", ...]}
```

Combine into the `tags` field as:
`[Tag: hashtag1], [Tag: hashtag2], keyword1, keyword2, keyword3`

### Step 4: Regenerate CSV

After updating classification, hook, and tags in `scored.json`, re-run
`score.py` or a CSV regeneration step to produce the final `scored.csv`
with all fields populated.

Alternatively, use the orchestrator's Python script to regenerate CSV from
the updated JSON.

### Step 5: Save Trace

Write `classified.json` (just post_id + hook + classification + tags) to
`<run>/classified.json`. Log every LLM call to
`<run>/trace/classifier-<N>.json` (prompt + response, no truncation).

## Pitfalls

- **LLM hallucinates labels**: Always validate returned labels against the
  taxonomy list. Retry once, then fall back to "Lainnya".
- **Hook too long**: The deterministic extractor enforces 80-char limit,
  but if the caption has no sentence breaks it may truncate mid-word.
  The QA skill will catch hooks > 80 chars.
- **Empty caption**: Posts without caption.text get empty hooks and
  classification "Lainnya". Skip LLM calls for these.
- **Algorithmic tags empty**: Not all posts have hashtag fragments. This
  is fine — the content keywords from LLM still populate the tags field.

## Verification

1. Confirm `HOOK <N>` printed with N > 0.
2. Check that every post in `scored.json` has a non-empty hook field.
3. Verify all classification labels are in `taxonomy.yaml` (spot check).
4. Check that `classified.json` contains one entry per post.
5. Open `scored.csv` and verify that Klasifikasi Topik and Tags columns
   are populated.
