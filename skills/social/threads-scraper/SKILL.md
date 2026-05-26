---
name: threads-scraper
description: |
  Calls scrapecreators.com /v1/threads/search for one keyword at a time over
  a date range. Handles retries with exponential backoff, response caching by
  query hash, deduplication by post_id, and filtering of replies and paid
  promos. Does NOT score or classify — those are separate skills.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [Social, Threads, Scraper, API]
required_environment_variables:
  - name: SCRAPECREATORS_API_KEY
    prompt: scrapecreators.com primary API key
    required_for: Threads search endpoint
  - name: SCRAPECREATORS_API_KEY_2
    prompt: scrapecreators.com secondary API key (optional — fallback rotation)
    required_for: Auto-rotated on 401/403/429
---

# Threads Scraper

Scrapes Threads posts via scrapecreators.com API for a single keyword over
a date range. Handles caching, retries, dedup, and filtering — outputs clean
post list ready for scoring.

## When to Use

- You have a list of keywords and a date range to search.
- You need raw Threads data cleaned of replies, promos, and low-engagement
  noise before analysis.
- Called by the orchestrator — not typically invoked directly.

## Quick Reference

| Step | Script | Input | Output |
|------|--------|-------|--------|
| 1. Scrape | `scrape.py --query Q --start D --end D --run-dir DIR` | `SCRAPECREATORS_API_KEY` | `<run>/raw/<slug>.json` |
| 2. Dedup | `dedup.py --run-dir DIR` | `<run>/raw/*.json` | `<run>/deduped-pre-filter.json` |
| 3. Filter | `filter.py --run-dir DIR` | `<run>/deduped-pre-filter.json` | `<run>/deduped.json` |

Cache TTL: 24 hours per unique query+date combination (SHA256 keyed).

## Procedure

1. **For each keyword**, invoke `scrape.py` individually:
   ```
   python <skill_dir>/scripts/scrape.py --query "<keyword>" --start <start> --end <end> --run-dir <run>
   ```
   - The script handles caching — if a cached response exists and is < 24h old,
     it copies it rather than hitting the API.
   - On API failure after 4 retries: log the error to `<run-dir>/run-summary.md`
     (if the orchestrator created it) and skip that keyword.

2. **Deduplicate**:
   ```
   python <skill_dir>/scripts/dedup.py --run-dir <run>
   ```
   - Combines all per-keyword raw files into one list.
   - Dedupes by `post_id` (keeps first occurrence).
   - Adds `matched_keywords` (list) and `source_queries` (list) to each post.

3. **Filter**:
   ```
   python <skill_dir>/scripts/filter.py --run-dir <run>
   ```
   Removes posts where:
   - `text_post_app_info.is_reply == true`
   - `is_paid_partnership == true`
   - `like_count + direct_reply_count + reshare + repost + quote < 5`

Final artifact: `<run>/deduped.json` — ready for the scorer.

## Pitfalls

- **API key missing**: scrape.py exits 1 with "FATAL: neither SCRAPECREATORS_API_KEY nor SCRAPECREATORS_API_KEY_2 is set". Verify at least one env var is set before invoking.
- **Multi-key rotation**: If `SCRAPECREATORS_API_KEY_2` is also set, the script auto-rotates to it on 401/403/429 responses from the primary key. Both keys must be valid.
- **Cache stampede**: If multiple keywords produce identical cache keys (same query+date),
  the second invocation copies from cache instantly — no duplicate API calls.
- **Empty raw directory**: If all keywords fail their API calls, dedup.py warns and
  produces an empty deduped-pre-filter.json. The orchestrator should check counts.
- **Filter removes everything**: If engagement floor (5 interactions) is too aggressive
  for a short date range, reduce the threshold or widen the range.
- **API field changes**: The scraper consumes specific fields (like_count, is_reply,
  text_post_app_info.*). If the API changes these, the script may silently produce
  zero or broken data. Check the API response shape with a manual curl first.

## Verification

1. Check that `scrape.py` prints `OK <query> <N>` for each keyword.
2. Verify `<run>/raw/<slug>.json` exists with real posts.
3. Run `dedup.py` and confirm `DEDUP <in> -> <out>` shows dedup reduced the count.
4. Run `filter.py` and confirm `FILTER <in> -> <out>` with reasonable removal counts.
5. Inspect `<run>/deduped.json` — each post should have `matched_keywords` and
   `source_queries` arrays populated.
