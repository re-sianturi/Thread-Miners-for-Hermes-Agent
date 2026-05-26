# Formulas

## Scoring Fields

```
L            = like_count                                       (int)
C            = text_post_app_info.direct_reply_count            (int)
R            = text_post_app_info.reshare_count
             + text_post_app_info.repost_count
             + text_post_app_info.quote_count                   (int, sum)
tot_int      = L + C + R
point        = 1*L + 2*C + 3*R
viralitas    = R / tot_int    if tot_int > 0 else 0.0
eng_density  = C / L          if L > 0       else None (display "N/A")
age_days     = max(1, floor((now - taken_at) / 86400))
evg_score    = point / age_days
```

## Design Notes

The user's original brief specifies `1L + 2C + 3R` for ranking. Their
example table appears to display `Evg.Score = Tot.Int / Age` instead.
This implementation follows the brief (weighted Point) because comments
and reshares are stronger quality signals than passive likes.

Both `tot_int` and `point` are persisted in `scored.json`, so any consumer
can resort by either. `age_days` is floored at 1 day (anti div-by-zero).
Posts younger than 7 days are flagged "unstable" in `run-summary.md`
because their engagement hasn't normalized.

## Output Fields in scored.json

| Field | Type | Description |
|-------|------|-------------|
| post_id | string | Unique post identifier |
| username | string | Poster's handle |
| code | string | Post shortcode |
| url | string | Full URL to post |
| caption | string | Full caption text |
| like_count | int | L |
| reply_count | int | C |
| reshare_repost_quote | int | R (sum of reshare+repost+quote) |
| tot_int | int | L + C + R |
| point | int | 1L + 2C + 3R |
| viralitas | float | R / tot_int |
| eng_density | float or null | C / L |
| age_days | int | Post age, min 1 |
| evg_score | float | point / age_days |
| media_format | string | Carousel / Video / Gambar / Teks |
| matched_keywords | list | Keywords that matched this post |
| source_queries | list | Queries that returned this post |
| alg_tags | list | Hashtags from API fragments |
| classification | string | Filled by classifier |
| hook | string | Filled by classifier |
| tags | string | Combined tag string |
