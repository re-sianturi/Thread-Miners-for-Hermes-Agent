#!/usr/bin/env python3
"""
Usage: filter.py --run-dir DIR

Reads <run-dir>/deduped-pre-filter.json. Removes replies, paid promos, and
low-engagement posts. Writes <run-dir>/deduped.json.

Requirements: pip install PyYAML
"""

import argparse, json, os, sys


def get_nested(obj, path, default=None):
    """Safely traverse nested dicts with dot-separated path."""
    parts = path.split(".")
    current = obj
    for p in parts:
        if isinstance(current, dict):
            current = current.get(p, {})
        elif isinstance(current, list):
            if p.isdigit():
                idx = int(p)
                current = current[idx] if idx < len(current) else {}
            else:
                return default
        else:
            return default
    return current if current != {} else default


def main():
    parser = argparse.ArgumentParser(description="Filter scraped posts")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    in_path = os.path.join(run_dir, "deduped-pre-filter.json")

    if not os.path.exists(in_path):
        print(f"FATAL: {in_path} not found. Run dedup.py first.", file=sys.stderr)
        sys.exit(1)

    with open(in_path) as f:
        posts = json.load(f)

    reasons = {"is_reply": 0, "paid_partnership": 0, "low_engagement": 0}
    kept = []

    for post in posts:
        is_reply = get_nested(post, "text_post_app_info.is_reply", False)
        is_paid = post.get("is_paid_partnership", False)
        like_count = get_nested(post, "like_count", 0)
        reply_count = get_nested(post, "text_post_app_info.direct_reply_count", 0)
        reshare = get_nested(post, "text_post_app_info.reshare_count", 0)
        repost = get_nested(post, "text_post_app_info.repost_count", 0)
        quote = get_nested(post, "text_post_app_info.quote_count", 0)
        total_eng = like_count + reply_count + reshare + repost + quote

        if is_reply:
            reasons["is_reply"] += 1
            continue
        if is_paid:
            reasons["paid_partnership"] += 1
            continue
        if total_eng < 5:
            reasons["low_engagement"] += 1
            continue

        kept.append(post)

    out_path = os.path.join(run_dir, "deduped.json")
    with open(out_path, "w") as f:
        json.dump(kept, f, indent=2, ensure_ascii=False)

    removed_detail = ", ".join(f"{k}={v}" for k, v in reasons.items() if v > 0)
    print(f"FILTER {len(posts)} -> {len(kept)}, removed: {removed_detail}")
    sys.exit(0)


if __name__ == "__main__":
    main()
