#!/usr/bin/env python3
"""
Usage: apply_fixes.py --run-dir DIR

Reads qa/fixes.yaml. Applies {post_id, field, after} changes to scored.json.
Whitelist: hook, tags, classification only. Rejects numeric field changes.
On success regenerates scored.csv. Exit 0.

Requirements: pip install PyYAML
"""

import argparse, csv, json, os, sys, yaml

FIXABLE_FIELDS = {"hook", "tags", "classification"}
CSV_COLS = [
    "Akun", "Teks Hook (Pancingan Pertama)", "L / C / R", "Tot. Int.",
    "Viralitas (R/Tot)", "Eng. Density (C/L)", "Usia (Hari)",
    "Evg. Score", "Format Media", "Klasifikasi Topik",
    "Tags Algoritma & Keywords",
]


def regenerate_csv(scored, csv_path):
    """Regenerate scored.csv from scored.json."""
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(CSV_COLS)
        for r in scored:
            lcr = f"{r.get('like_count', 0)} / {r.get('reply_count', 0)} / {r.get('reshare_repost_quote', 0)}"
            viral = r.get("viralitas", 0)
            viral_str = f"{viral*100:.1f}%" if viral else "0%"
            ed = r.get("eng_density")
            eng_str = f"{ed:.2f}" if ed is not None else "N/A"
            w.writerow([
                f"@{r.get('username', '?')}",
                r.get("hook", ""),
                lcr,
                str(r.get("tot_int", 0)),
                viral_str,
                eng_str,
                str(r.get("age_days", 0)),
                f"{r.get('evg_score', 0):.2f}",
                r.get("media_format", ""),
                r.get("classification", ""),
                r.get("tags", ""),
            ])


def main():
    parser = argparse.ArgumentParser(description="Apply QA fixes to scored.json")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    fixes_path = os.path.join(run_dir, "qa", "fixes.yaml")
    scored_path = os.path.join(run_dir, "scored.json")

    if not os.path.exists(fixes_path):
        print("NO_FIXES nothing to apply")
        sys.exit(0)

    if not os.path.exists(scored_path):
        print(f"FATAL: {scored_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(fixes_path) as f:
        fixes = yaml.safe_load(f)

    if not fixes or not isinstance(fixes, list):
        print("NO_FIXES empty or invalid fixes.yaml")
        sys.exit(0)

    with open(scored_path) as f:
        scored = json.load(f)

    # Build post_id index
    index = {p.get("post_id", "?"): p for p in scored}
    applied = []

    for fix in fixes:
        pid = fix.get("post_id")
        field = fix.get("field")
        after = fix.get("after")

        if not pid:
            print(f"WARN: fix missing post_id: {fix}", file=sys.stderr)
            continue
        if field not in FIXABLE_FIELDS:
            print(f"FATAL: field '{field}' not in whitelist {FIXABLE_FIELDS}", file=sys.stderr)
            sys.exit(1)
        if pid not in index:
            print(f"WARN: post_id '{pid}' not found in scored.json, skipping", file=sys.stderr)
            continue

        before = index[pid].get(field, "")
        index[pid][field] = after
        applied.append({"post_id": pid, "field": field, "before": before, "after": after})
        print(f"  FIX {pid}.{field}: '{before[:40]}...' -> '{after[:40]}...'")

    # Write updated scored.json
    with open(scored_path, "w") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)

    # Regenerate CSV
    csv_path = os.path.join(run_dir, "scored.csv")
    regenerate_csv(scored, csv_path)

    print(f"APPLIED {len(applied)} fixes")
    sys.exit(0)


if __name__ == "__main__":
    main()
