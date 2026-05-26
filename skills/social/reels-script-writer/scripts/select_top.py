#!/usr/bin/env python3
"""
Usage: select_top.py --run-dir DIR --max N

Filters reel-ready candidates from scored.json, sorts by Evg.Score, takes
top N (default 3). Reads taxonomy.yaml from the reels-script-writer skill's
own references/ directory to determine reel_ready status.

Requirements: pip install PyYAML
"""

import argparse, json, os, sys, yaml


def main():
    parser = argparse.ArgumentParser(description="Select top reel-ready candidates")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--max", type=int, default=3)
    args = parser.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    scored_path = os.path.join(run_dir, "scored.json")
    if not os.path.exists(scored_path):
        print(f"FATAL: {scored_path} not found. Run classifier + QA first.", file=sys.stderr)
        sys.exit(1)

    # Load taxonomy from THIS skill's references
    ref_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
    tax_path = os.path.join(ref_dir, "taxonomy.yaml")
    if not os.path.exists(tax_path):
        # Fallback: try classifier's taxonomy
        tax_path = os.path.join(os.path.dirname(run_dir), "..", "..", "threads-classifier", "references", "taxonomy.yaml")
        if not os.path.exists(tax_path):
            print(f"FATAL: taxonomy.yaml not found", file=sys.stderr)
            sys.exit(1)

    with open(tax_path) as f:
        taxonomy = yaml.safe_load(f)

    reel_ready_labels = set()
    for cat in taxonomy.get("categories", []):
        if cat.get("reel_ready"):
            reel_ready_labels.add(cat["label"])

    with open(scored_path) as f:
        posts = json.load(f)

    eligible = []
    total_passed = 0

    for p in posts:
        cls = p.get("classification", "")
        hook = p.get("hook", "")
        ti = p.get("tot_int", 0)
        evg = p.get("evg_score", 0)
        ad = p.get("age_days", 0)
        mf = p.get("media_format", "Teks")

        # Filter conditions
        if cls not in reel_ready_labels:
            continue
        if not (15 <= len(hook) <= 80):
            continue
        if ti < 30:
            continue
        if evg < 1.0:
            continue
        if ad > 60:
            continue

        total_passed += 1

        # Media format: Teks allowed only as fallback
        # We separate by media type
        p["_candidate_media_rank"] = 0 if mf in ("Carousel", "Gambar", "Video") else 1
        eligible.append(p)

    # Sort: media rank (0 before 1), then evg_score desc
    eligible.sort(key=lambda x: (x["_candidate_media_rank"], -x["evg_score"]))

    selected = eligible[:args.max]
    shortfall = args.max - len(selected)

    # Write top.json
    out_path = os.path.join(run_dir, "top.json")
    # Clean internal fields
    for s in selected:
        s.pop("_candidate_media_rank", None)
    with open(out_path, "w") as f:
        json.dump(selected, f, indent=2, ensure_ascii=False)

    msg = f"TOP {len(selected)} of {total_passed}"
    if shortfall > 0:
        msg += f" (shortfall: {shortfall})"
    print(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
