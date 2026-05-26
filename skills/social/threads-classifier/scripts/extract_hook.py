#!/usr/bin/env python3
"""
Usage: extract_hook.py --run-dir DIR

For each post in scored.json, extracts the hook (first sentence or first 80
chars). Deterministic — no LLM calls. Writes hooks back into scored.json.

Requirements: pip install PyYAML
"""

import argparse, json, os, sys, re


def extract_hook(text):
    if not text or not text.strip():
        return ""

    text = text.strip()
    # First sentence: split on sentence terminators followed by whitespace/end
    m = re.match(r"(.+?[.!?])(?:\s+|$)", text, re.DOTALL)
    first = m.group(1) if m else text

    if len(first) > 80:
        # Truncate at last word boundary before char 77, append "..."
        cut = first[:77].rsplit(" ", 1)[0]
        return cut + "..."
    elif len(first) < 15:
        # Too short, take first 80 chars of full text
        hook = text[:80].rsplit(" ", 1)[0]
        if len(hook) < len(text):
            hook += "..."
        return hook
    else:
        return first.strip()


def main():
    parser = argparse.ArgumentParser(description="Extract hooks from scored posts")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    in_path = os.path.join(run_dir, "scored.json")
    if not os.path.exists(in_path):
        print(f"FATAL: {in_path} not found. Run scorer first.", file=sys.stderr)
        sys.exit(1)

    with open(in_path) as f:
        posts = json.load(f)

    count = 0
    for post in posts:
        caption = post.get("caption", "")
        hook = extract_hook(caption)
        post["hook"] = hook
        if hook:
            count += 1

    # Write updated scored.json
    with open(in_path, "w") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    # Write classified.json (trace-only)
    classified = [{"post_id": p["post_id"], "hook": p["hook"]} for p in posts]
    cls_path = os.path.join(run_dir, "classified.json")
    with open(cls_path, "w") as f:
        json.dump(classified, f, indent=2, ensure_ascii=False)

    print(f"HOOK {count}")
    sys.exit(0)


if __name__ == "__main__":
    main()
