#!/usr/bin/env python3
"""
Usage: new_run.py --output-dir DIR --keywords K1,K2,... --start YYYY-MM-DD --end YYYY-MM-DD

Creates <output-dir>/<ISO-timestamp>-<first-keyword-slug>/.
Writes config.yaml with all inputs.
Prints absolute run path to stdout.

Requirements: pip install PyYAML
"""

import argparse, os, sys, time, yaml


def slugify(text):
    safe = "".join(c if c.isalnum() else "_" for c in text.lower().strip())
    return safe[:40]


def main():
    parser = argparse.ArgumentParser(description="Create a new Threads Miner run folder")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        print("FATAL: at least one keyword required", file=sys.stderr)
        sys.exit(1)

    output_dir = os.path.abspath(os.path.expanduser(args.output_dir))
    ts = time.strftime("%Y-%m-%dT%H-%M")
    first_slug = slugify(keywords[0])
    run_name = f"{ts}-{first_slug}"
    run_dir = os.path.join(output_dir, run_name)

    try:
        os.makedirs(run_dir)
        os.makedirs(os.path.join(run_dir, "raw"))
        os.makedirs(os.path.join(run_dir, "qa"))
        os.makedirs(os.path.join(run_dir, "reels"))
        os.makedirs(os.path.join(run_dir, "trace"))
    except OSError as e:
        print(f"FATAL: cannot create run dir: {e}", file=sys.stderr)
        sys.exit(1)

    # Write config
    config = {
        "run_name": run_name,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "keywords": keywords,
        "date_range": {"start": args.start, "end": args.end},
        "formula_version": "1.0",
        "status": "new",
    }
    config_path = os.path.join(run_dir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(run_dir)
    sys.exit(0)


if __name__ == "__main__":
    main()
