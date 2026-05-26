#!/usr/bin/env python3
"""
Usage: score.py --run-dir DIR

Reads <run-dir>/deduped.json. Computes scoring metrics for each post.
Outputs scored.json (full fields) and scored.csv (user-facing columns).

Requirements: pip install PyYAML
"""

import argparse, csv, json, os, sys, time, math


def get_nested(obj, path, default=0):
    parts = path.split(".")
    current = obj
    for p in parts:
        if isinstance(current, dict):
            current = current.get(p)
            if current is None:
                return default
        elif isinstance(current, list):
            if p.isdigit():
                idx = int(p)
                current = current[idx] if idx < len(current) else default
                break
            return default
        else:
            return default
    return current if current is not None else default


def derive_media_format(post):
    if post.get("carousel_media") is not None:
        return "Carousel"
    if post.get("video_versions"):
        return "Video"
    img = get_nested(post, "image_versions2.candidates", None)
    if img and len(img) > 0:
        return "Gambar"
    return "Teks"


def main():
    parser = argparse.ArgumentParser(description="Score scraped posts")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    in_path = os.path.join(run_dir, "deduped.json")
    if not os.path.exists(in_path):
        print(f"FATAL: {in_path} not found. Run scraper first.", file=sys.stderr)
        sys.exit(1)

    with open(in_path) as f:
        posts = json.load(f)

    now = time.time()
    scored = []

    for post in posts:
        pid = post.get("post_id") or post.get("id") or post.get("code", "?")
        username = post.get("username", "?")
        code = post.get("code", "")
        url = f"https://threads.net/@{username}/post/{code}" if code else ""
        caption = get_nested(post, "caption.text", "")
        taken_at = post.get("taken_at", now)
        like_count = int(get_nested(post, "like_count", 0))
        reply_count = int(get_nested(post, "text_post_app_info.direct_reply_count", 0))
        reshare = int(get_nested(post, "text_post_app_info.reshare_count", 0))
        repost = int(get_nested(post, "text_post_app_info.repost_count", 0))
        quote = int(get_nested(post, "text_post_app_info.quote_count", 0))
        r_total = reshare + repost + quote
        tot_int = like_count + reply_count + r_total
        point = (1 * like_count) + (2 * reply_count) + (3 * r_total)
        viralitas = r_total / tot_int if tot_int > 0 else 0.0
        eng_density = reply_count / like_count if like_count > 0 else None
        age_seconds = now - taken_at
        age_days = max(1, int(age_seconds // 86400))
        evg_score = point / age_days
        media_format = derive_media_format(post)

        # Extract algorithmic tags (hashtags from API)
        fragments = get_nested(post, "text_post_app_info.text_fragments.fragments", [])
        alg_tags = []
        if isinstance(fragments, list):
            for f in fragments:
                if isinstance(f, dict) and f.get("fragment_type") == "tag":
                    alg_tags.append(f.get("text", ""))

        row = {
            "post_id": pid,
            "username": username,
            "code": code,
            "url": url,
            "caption": caption,
            "like_count": like_count,
            "reply_count": reply_count,
            "reshare_repost_quote": r_total,
            "tot_int": tot_int,
            "point": point,
            "viralitas": viralitas,
            "eng_density": eng_density,
            "age_days": age_days,
            "evg_score": round(evg_score, 2),
            "media_format": media_format,
            "matched_keywords": post.get("matched_keywords", []),
            "source_queries": post.get("source_queries", []),
            "alg_tags": alg_tags,
            "classification": "",
            "hook": "",
            "tags": "",
        }
        scored.append(row)

    # Sort by evg_score descending
    scored.sort(key=lambda r: r["evg_score"], reverse=True)

    # Write scored.json
    scored_path = os.path.join(run_dir, "scored.json")
    with open(scored_path, "w") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)

    # Write scored.csv
    csv_path = os.path.join(run_dir, "scored.csv")
    csv_cols = [
        "Akun", "Teks Hook (Pancingan Pertama)", "L / C / R", "Tot. Int.",
        "Viralitas (R/Tot)", "Eng. Density (C/L)", "Usia (Hari)",
        "Evg. Score", "Format Media", "Klasifikasi Topik",
        "Tags Algoritma & Keywords",
    ]
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(csv_cols)
        for r in scored:
            lcr = f"{r['like_count']} / {r['reply_count']} / {r['reshare_repost_quote']}"
            viral_str = f"{r['viralitas']*100:.1f}%" if r['viralitas'] else "0%"
            eng_str = f"{r['eng_density']:.2f}" if r['eng_density'] is not None else "N/A"
            w.writerow([
                f"@{r['username']}",
                r["hook"],
                lcr,
                str(r["tot_int"]),
                viral_str,
                eng_str,
                str(r["age_days"]),
                f"{r['evg_score']:.2f}",
                r["media_format"],
                r["classification"],
                r["tags"],
            ])

    print(f"SCORED {len(scored)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
