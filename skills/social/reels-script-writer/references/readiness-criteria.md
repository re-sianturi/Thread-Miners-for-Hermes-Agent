# Readiness Criteria for Reel Candidates

A post passes the candidate filter only if ALL conditions hold:

1. **Reel-ready classification**: The post's topic (from taxonomy.yaml)
   has `reel_ready: true`. Non-reel categories (Networking, Hiring,
   Kolaborasi, Promosi, Opini Singkat, Lainnya) are excluded.

2. **Hook length**: Between 15 and 80 characters. Too short (< 15) doesn't
   grab attention. Too long (> 80) can't fit in a 3-second hook graphic.

3. **Minimum total engagement**: `tot_int >= 30`. Posts with fewer
   interactions likely won't resonate as reel content.

4. **Minimum engagement score**: `evg_score >= 1.0`. The weighted score
   (point / age_days) must be at least 1.0 — weaker posts are excluded.

5. **Maximum age**: `age_days <= 60`. Posts older than 2 months are stale;
   audiences prefer current content.

6. **Media format**: Carousel, Gambar, or Video preferred. Teks-only posts
   are allowed only as fallback if not enough media-rich candidates exist.

## Worked Example

A post with:
- classification: "Edukasi (Framework)" → reel_ready = YES
- hook: "Framework belajar AI buat pemula" → 35 chars → PASS
- tot_int: 154 → PASS (>= 30)
- evg_score: 3.2 → PASS (>= 1.0)
- age_days: 45 → PASS (<= 60)
- media_format: "Carousel" → PASS

**Result: Candidate**

---

A post with:
- classification: "Hiring (B2B)" → reel_ready = NO
- hook: "Cari freelancer AI? DM gue" → 28 chars → would pass
- tot_int: 89 → PASS

**Result: REJECTED** — classification is not reel-ready.
