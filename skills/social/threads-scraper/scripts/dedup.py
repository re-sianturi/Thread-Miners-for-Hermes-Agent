#!/usr/bin/env python3
"""
Usage: dedup.py --run-dir DIR

Reads all files in <run-dir>/raw/*.json. Combines posts into a single list.
Dedupes by post_id (keeping the first occurrence). Adds matched_keywords and
source_queries fields aggregated from per-keyword files.
Writes <run-dir>/deduped-pre-filter.json.

Requirements: pip install PyYAML
"""

import argparse, json, os, sys, glob


def main():
    parser = argparse.ArgumentParser(description="Deduplicate scraped posts")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    raw_dir = os.path.join(run_dir, "raw")
    if not os.path.isdir(raw_dir):
        print(f"FATAL: raw dir not found: {raw_dir}", file=sys.stderr)
        sys.exit(1)

    # Gather all posts with keyword tracking
    seen = {}       # post_id -> (post, keywords, queries)
    total_in = 0

    for fpath in sorted(glob.glob(os.path.join(raw_dir, "*.json"))):
        fname = os.path.splitext(os.path.basename(fpath))[0]
        try:
            with open(fpath) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: skipping {fpath}: {e}", file=sys.stderr)
            continue

        items = data.get("data", {}).get("items", data.get("items", []))
        if not items:
            # try alternate structure
            items = data.get("items", [])

        for post in items:
            total_in += 1
            pid = post.get("id") or post.get("post_id") or post.get("code")
            if not pid:
                continue
            if pid in seen:
                existing_post, existing_kws, existing_queries = seen[pid]
                if fname not in existing_kws:
                    existing_kws.append(fname)
                if fname not in existing_queries:
                    existing_queries.append(fname)
            else:
                seen[pid] = [post, [fname], [fname]]

    # Build deduped list with aggregated metadata
    deduped = []
    for pid, (post, keywords, queries) in seen.items():
        post["matched_keywords"] = keywords
        post["source_queries"] = queries
        # Normalize id field
        if "post_id" not in post:
            post["post_id"] = pid
        deduped.append(post)

    out_path = os.path.join(run_dir, "deduped-pre-filter.json")
    with open(out_path, "w") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"DEDUP {total_in} -> {len(deduped)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
